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
            try:
                # network on first use only; keys are cached afterwards
                signing_key = await asyncio.to_thread(self._jwks.get_signing_key_from_jwt, token)
            except jwt.PyJWTError as exc:
                raise ApiError("unauthenticated", "the token's signing key is not known") from exc
            key = signing_key.key
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
        email = claims.get("email")
        return AuthenticatedUser(id=user_id, email=email.lower() if email else None,
                                 role=str(claims.get("role") or AUDIENCE), claims=claims)


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
