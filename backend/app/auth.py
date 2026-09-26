"""Who is calling.

Supabase Auth issues the login token; this module verifies it and nothing else is
trusted for identity. Verification means signature, issuer, audience and expiry
(integration readiness §5). A token that merely decodes is not a login.

    ES256 / RS256   the project's public keys, fetched once from
                    SUPABASE_URL/auth/v1/.well-known/jwks.json and cached
    HS256           the legacy shared secret, only when SUPABASE_JWT_SECRET is set

The user id is the token's `sub`. Request bodies never carry a user id.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.errors import ApiError

AUDIENCE = "authenticated"
ASYMMETRIC = ("ES256", "RS256")
LEEWAY_SECONDS = 30
UNKNOWN_KID_SECONDS = 300
KEY_CACHE_SECONDS = 3600              # a verified signing key is reused this long (PyJWKClient keeps the set as long)
UNKNOWN_KID_REFRESH_SECONDS = 30      # at most one key-set fetch per this period is caused by an unknown `kid`
MAX_UNKNOWN_KIDS = 1024               # remembered unknown kids; anyone can send tokens with made-up kids


@dataclass(frozen=True)
class AuthenticatedUser:
    id: uuid.UUID
    email: str | None
    role: str
    claims: dict = field(default_factory=dict, repr=False, compare=False)

    @property
    def display_name(self) -> str | None:
        meta = self.claims.get("user_metadata") or {}
        return meta.get("full_name") or meta.get("name") or meta.get("display_name")


class TokenVerifier:
    def __init__(self, *, supabase_url: str | None, jwt_secret: str | None = None, jwks_client=None,
                 leeway: int = LEEWAY_SECONDS):
        self.issuer = supabase_url.rstrip("/") + "/auth/v1" if supabase_url else None
        self.jwt_secret = jwt_secret
        self.leeway = leeway
        if jwks_client is None and self.issuer:
            jwks_client = jwt.PyJWKClient(self.issuer + "/.well-known/jwks.json", cache_keys=True, lifespan=3600)
        self._jwks = jwks_client
        self._unknown_kids: dict[str | None, float] = {}
        # kid -> (fetched at, key): a known key is used on the event loop, without a thread hop per request
        self._keys: dict[str | None, tuple[float, object]] = {}
        self._last_miss_fetch = -1e9

    @property
    def configured(self) -> bool:
        return self._jwks is not None or self.jwt_secret is not None

    async def verify(self, token: str) -> AuthenticatedUser:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise ApiError("unauthenticated", "the token is malformed") from exc
        algorithm = header.get("alg")
        if algorithm in ASYMMETRIC and self._jwks is not None:
            key = await self._signing_key(token, header.get("kid"))
        elif algorithm == "HS256" and self.jwt_secret:
            key = self.jwt_secret
        else:
            raise ApiError("unauthenticated", f"tokens signed with {algorithm or 'no algorithm'} are not accepted")
        try:
            claims = jwt.decode(
                token, key, algorithms=[algorithm], audience=AUDIENCE, issuer=self.issuer, leeway=self.leeway,
                options={"require": ["exp", "sub", "aud"], "verify_iss": self.issuer is not None})
        except jwt.ExpiredSignatureError as exc:
            raise ApiError("unauthenticated", "the session has expired; sign in again") from exc
        except jwt.PyJWTError as exc:
            raise ApiError("unauthenticated", "the token could not be verified") from exc
        try:
            user_id = uuid.UUID(str(claims["sub"]))
        except ValueError as exc:
            raise ApiError("unauthenticated", "the token has no valid user id") from exc
        if claims.get("is_anonymous"):
            raise ApiError("unauthenticated", "anonymous sessions cannot practise")
        if (claims.get("user_metadata") or {}).get("email_verified") is False:
            raise ApiError("unauthenticated", "confirm your e-mail address first")
        email = claims.get("email")
        return AuthenticatedUser(id=user_id, email=email.lower() if email else None,
                                 role=str(claims.get("role") or AUDIENCE), claims=claims)

    async def _signing_key(self, token: str, kid: str | None):
        """The project's public key for this token's `kid`.

        A key verified before is reused from memory. Otherwise the key set is looked up in a worker thread (a
        network fetch when PyJWKClient's own cache misses). A `kid` the project does not have makes PyJWKClient
        refetch the whole key set, so such fetches are limited to one per UNKNOWN_KID_REFRESH_SECONDS: tokens
        with made-up kids (anyone can send them) cannot turn every request into a JWKS download and a busy thread."""
        now = time.monotonic()
        cached = self._keys.get(kid)
        if cached is not None and now - cached[0] < KEY_CACHE_SECONDS:
            return cached[1]
        if kid in self._unknown_kids and now - self._unknown_kids[kid] < UNKNOWN_KID_SECONDS:
            raise ApiError("unauthenticated", "the token's signing key is not known")
        if self._keys and now - self._last_miss_fetch < UNKNOWN_KID_REFRESH_SECONDS:
            self._remember_unknown(kid, now)                     # keys are known and a refresh just happened
            raise ApiError("unauthenticated", "the token's signing key is not known")
        if self._keys:
            self._last_miss_fetch = now
        try:
            signing_key = await asyncio.to_thread(self._jwks.get_signing_key_from_jwt, token)
        except jwt.PyJWTError as exc:
            self._remember_unknown(kid, now)                     # do not refetch the JWKS for this kid again soon
            raise ApiError("unauthenticated", "the token's signing key is not known") from exc
        self._keys[kid] = (now, signing_key.key)
        return signing_key.key

    def _remember_unknown(self, kid: str | None, now: float) -> None:
        if len(self._unknown_kids) >= MAX_UNKNOWN_KIDS:
            self._unknown_kids = {k: t for k, t in self._unknown_kids.items() if now - t < UNKNOWN_KID_SECONDS}
            if len(self._unknown_kids) >= MAX_UNKNOWN_KIDS:
                self._unknown_kids.clear()
        self._unknown_kids[kid] = now


_bearer = HTTPBearer(auto_error=False)


async def current_user(request: Request, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
                       ) -> AuthenticatedUser:
    """FastAPI dependency: the verified caller, or 401."""
    verifier: TokenVerifier | None = getattr(request.app.state, "verifier", None)
    if verifier is None or not verifier.configured:
        raise ApiError("unauthenticated", "login verification is not configured on this server", status=503)
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise ApiError("unauthenticated", "sign in and send the access token as a Bearer token",
                       headers={"WWW-Authenticate": "Bearer"})
    return await verifier.verify(credentials.credentials)
