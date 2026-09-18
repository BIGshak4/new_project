"""A stand-in for Supabase Auth: a test signing key and tokens shaped like Supabase's."""

from __future__ import annotations

import time
import uuid

import jwt
from cryptography.hazmat.primitives.asymmetric import ec

from app.auth import TokenVerifier
from app.repo.users import Access

SUPABASE_URL = "https://test-project.supabase.co"
ISSUER = SUPABASE_URL + "/auth/v1"
KID = "test-key-1"

_private_key = ec.generate_private_key(ec.SECP256R1())
_other_private_key = ec.generate_private_key(ec.SECP256R1())


class _Key:
    def __init__(self, key):
        self.key = key


class FakeJWKSClient:
    """Knows one key id, like a project's JWKS endpoint."""

    def get_signing_key_from_jwt(self, token: str):
        header = jwt.get_unverified_header(token)
        if header.get("kid") != KID:
            raise jwt.PyJWKClientError("kid not found")
        return _Key(_private_key.public_key())


def make_verifier() -> TokenVerifier:
    return TokenVerifier(supabase_url=SUPABASE_URL, jwks_client=FakeJWKSClient())


def make_token(user_id: uuid.UUID | None = None, *, email: str | None = "tester@example.com",
               expires_in: int = 3600, audience: str = "authenticated", issuer: str = ISSUER,
               kid: str = KID, wrong_key: bool = False, algorithm: str = "ES256",
               extra: dict | None = None) -> tuple[uuid.UUID, str]:
    user_id = user_id or uuid.uuid4()
    now = int(time.time())
    claims = {"sub": str(user_id), "aud": audience, "iss": issuer, "iat": now, "exp": now + expires_in,
              "email": email, "role": "authenticated", "user_metadata": {"full_name": "Test User"},
              "session_id": str(uuid.uuid4()), **(extra or {})}
    key = _other_private_key if wrong_key else _private_key
    if algorithm == "HS256":
        return user_id, jwt.encode(claims, "not-the-secret", algorithm="HS256", headers={"kid": kid})
    return user_id, jwt.encode(claims, key, algorithm=algorithm, headers={"kid": kid})


def member_resolver(members: set[str], *, founders: set[str] = frozenset()):
    async def resolve(user) -> Access:
        email = user.email or ""
        return Access(user_id=user.id, email=user.email, is_member=email in members,
                      can_manage_tasks=email in founders, profile_created=False)
    return resolve
