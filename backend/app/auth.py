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
KEY_CACHE_SECONDS = 3600              # a key seen in the project's set is reused this long (PyJWKClient keeps the set as long)
KEY_SET_FRESH_SECONDS = 30            # after a lookup, the set counts as current this long: at most one lookup per period


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
        # kid -> (seen at, key), only kids of the project's real key set: used on the event loop, no thread per request
        self._keys: dict[str | None, tuple[float, object]] = {}
        self._lookup: asyncio.Future | None = None
        self._last_lookup = -1e9

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

        A key seen in the project's key set is reused from memory, without a thread per request. Otherwise the key set
        is looked up, one lookup at a time, in a worker thread (PyJWKClient downloads it when its own cache misses or
        does not hold the kid), and EVERY key of the set it saw is stored, so a lookup caused by anyone refreshes the
        real keys too. After a lookup the set counts as current for KEY_SET_FRESH_SECONDS: a kid not in it is refused
        without another download. Made-up kids (anyone can send them) therefore cost at most one lookup per
        KEY_SET_FRESH_SECONDS and can never lock a real key out; a key added to the project waits at most that long."""
        cached = self._keys.get(kid)
        if cached is not None and time.monotonic() - cached[0] < KEY_CACHE_SECONDS:
            return cached[1]
        if self._lookup is not None:                       # a lookup is on its way: its answer is this one's too
            await asyncio.shield(self._lookup)
        elif time.monotonic() - self._last_lookup >= KEY_SET_FRESH_SECONDS:
            self._last_lookup = time.monotonic()
            self._lookup = asyncio.ensure_future(self._look_up(token))
            try:
                await asyncio.shield(self._lookup)
            finally:
                self._lookup = None
        cached = self._keys.get(kid)
        if cached is not None and time.monotonic() - cached[0] < KEY_CACHE_SECONDS + KEY_SET_FRESH_SECONDS:
            return cached[1]
        raise ApiError("unauthenticated", "the token's signing key is not known")

    async def _look_up(self, token: str) -> None:
        found = await asyncio.to_thread(self._fetch_keys, token)
        now = time.monotonic()
        for kid, key in found.items():
            self._keys[kid] = (now, key)

    def _fetch_keys(self, token: str) -> dict:
        """(worker thread) {kid: key} for the token's kid if the project has it, and for every key of the set."""
        found = {}
        try:
            signing = self._jwks.get_signing_key_from_jwt(token)        # downloads the set when needed
            found[jwt.get_unverified_header(token).get("kid")] = signing.key
        except jwt.PyJWTError:
            pass                                                        # not in the project's set
        every = getattr(self._jwks, "get_signing_keys", None)
        if every is not None:
            try:
                for key in every():                                     # the set just seen, from the client's cache
                    found[key.key_id] = key.key
            except jwt.PyJWTError:
                pass
        return found


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
