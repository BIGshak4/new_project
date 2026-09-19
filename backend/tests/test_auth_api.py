"""Login verification and pilot access (integration readiness §5): every way a token can be wrong."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.main import app
from tests.authtools import ISSUER, make_token, make_verifier, member_resolver

MEMBER = "tester@example.com"


@pytest.fixture
async def client(monkeypatch):
    app.state.verifier = make_verifier()
    app.state.access_resolver = member_resolver({MEMBER, "founder@example.com"}, founders={"founder@example.com"})
    monkeypatch.setattr(get_settings(), "require_pilot_membership", True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestTokens:
    async def test_a_valid_token_identifies_the_user(self, client):
        user_id, token = make_token()
        body = (await client.get("/v1/me", headers=auth(token))).json()
        assert body == {"id": str(user_id), "email": MEMBER, "pilot_member": True, "can_manage_tasks": False}

    async def test_no_token_is_401_with_the_error_shape(self, client):
        response = await client.get("/v1/me")
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthenticated"
        assert response.headers["www-authenticate"] == "Bearer"

    @pytest.mark.parametrize("kwargs, reason", [
        ({"expires_in": -120}, "expired"),
        ({"audience": "anon"}, "wrong audience"),
        ({"issuer": "https://other-project.supabase.co/auth/v1"}, "wrong issuer"),
        ({"wrong_key": True}, "signed by another key"),
        ({"kid": "unknown"}, "unknown key id"),
        ({"algorithm": "HS256"}, "shared-secret token when the project uses public keys"),
        ({"extra": {"is_anonymous": True}}, "anonymous session"),
    ], ids=lambda v: v if isinstance(v, str) else "")
    async def test_bad_tokens_are_rejected(self, client, kwargs, reason):
        _, token = make_token(**kwargs)
        response = await client.get("/v1/me", headers=auth(token))
        assert response.status_code == 401, reason
        assert response.json()["error"]["code"] == "unauthenticated"

    async def test_garbage_is_401_not_500(self, client):
        for token in ("not.a.jwt", "", "eyJhbGciOiJub25lIn0.e30."):
            response = await client.get("/v1/me", headers=auth(token))
            assert response.status_code == 401

    async def test_the_user_id_comes_from_the_token_only(self, client):
        user_id, token = make_token()
        response = await client.get("/v1/me", headers=auth(token), params={"user_id": "someone-else"})
        assert response.json()["id"] == str(user_id)

    async def test_expiry_leeway_tolerates_clock_skew_only(self, client):
        _, fresh = make_token(expires_in=-5)              # 5 s past expiry: within leeway
        assert (await client.get("/v1/me", headers=auth(fresh))).status_code == 200
        _, stale = make_token(expires_in=-120)
        assert (await client.get("/v1/me", headers=auth(stale))).status_code == 401


class TestPilotAccess:
    async def test_a_signed_in_non_member_is_forbidden(self, client):
        _, token = make_token(email="stranger@example.com")
        response = await client.get("/v1/me", headers=auth(token))
        assert response.status_code == 403 and response.json()["error"]["code"] == "forbidden"

    async def test_membership_is_by_email_case_insensitively(self, client):
        _, token = make_token(email="Tester@Example.com")
        assert (await client.get("/v1/me", headers=auth(token))).json()["pilot_member"] is True

    async def test_founder_flag_is_reported_never_granted(self, client):
        _, token = make_token(email="founder@example.com")
        assert (await client.get("/v1/me", headers=auth(token))).json()["can_manage_tasks"] is True
        _, token = make_token(email=MEMBER)
        assert (await client.get("/v1/me", headers=auth(token))).json()["can_manage_tasks"] is False

    async def test_membership_can_be_switched_off_for_development(self, client, monkeypatch):
        monkeypatch.setattr(get_settings(), "require_pilot_membership", False)
        _, token = make_token(email="stranger@example.com")
        assert (await client.get("/v1/me", headers=auth(token))).status_code == 200


class TestServerConfiguration:
    async def test_unconfigured_verifier_is_503_not_open(self, client):
        from app.auth import TokenVerifier
        app.state.verifier = TokenVerifier(supabase_url=None)
        _, token = make_token()
        response = await client.get("/v1/me", headers=auth(token))
        assert response.status_code == 503

    def test_origins_are_parsed_from_a_comma_separated_string(self):
        settings = Settings(_env_file=None, allowed_origins="https://a.netlify.app/, https://b.netlify.app")
        assert settings.allowed_origins == ["https://a.netlify.app", "https://b.netlify.app"]

    def test_origins_are_read_from_the_env_file_path_too(self, tmp_path, monkeypatch):
        env = tmp_path / ".env"
        env.write_text("ALLOWED_ORIGINS=https://a.netlify.app, https://b.netlify.app\nDAILY_ATTEMPT_LIMIT=5\n")
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
        settings = Settings(_env_file=env)
        assert settings.allowed_origins == ["https://a.netlify.app", "https://b.netlify.app"]
        assert settings.daily_attempt_limit == 5
        assert Settings(_env_file=None, allowed_origins="").allowed_origins == []

    def test_production_refuses_to_run_half_configured(self):
        settings = Settings(_env_file=None, env="production")
        problems = settings.production_problems()
        assert any("DATABASE_URL" in p for p in problems) and any("SUPABASE_URL" in p for p in problems)
        ready = Settings(_env_file=None, env="production", supabase_url="https://x",
                         database_url="postgresql://postgres.abc:pw@aws-0-eu-central-1.pooler.supabase.com:5432/postgres",
                         allowed_origins="https://a", llm_provider="anthropic", anthropic_api_key="k")
        assert ready.production_problems() == []

    def test_the_direct_database_host_is_flagged(self):
        direct = Settings(_env_file=None, database_url="postgresql://postgres:x@db.abcdefghij.supabase.co:5432/postgres")
        pooler = Settings(_env_file=None, database_url="postgresql://postgres.abc:x@aws-0-eu-central-1.pooler.supabase.com:5432/postgres")
        assert direct.database_host_kind == "direct" and pooler.database_host_kind == "pooler"
        assert any("IPv6" in p for p in direct.production_problems())
        assert not any("IPv6" in p for p in pooler.production_problems())

    @pytest.mark.parametrize("url, expected", [
        ("postgresql://postgres:pw@aws-0-eu-central-1.pooler.supabase.com:5432/postgres", "postgres.<project-ref>"),
        ("postgresql://postgres.abc:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:5432/postgres", "placeholder"),
        ("postgresql://postgres.abc:p#w@aws-0-eu-central-1.pooler.supabase.com:5432/postgres", "percent-encoded"),
        ("postgresql://postgres.abc:goodpw@aws-0-eu-central-1.pooler.supabase.com:5432/postgres", None),
    ], ids=["plain-user-on-pooler", "placeholder", "unencoded", "fine"])
    def test_connection_string_mistakes_are_named(self, url, expected):
        problems = Settings(_env_file=None, database_url=url).database_url_problems()
        if expected is None:
            assert problems == []
        else:
            assert any(expected in p for p in problems), problems

    def test_issuer_is_derived_from_the_project_url(self):
        assert make_verifier().issuer == ISSUER


class TestHealth:
    async def test_health_reports_configuration_not_values(self, client):
        body = (await client.get("/health")).json()
        assert body["status"] == "ok" and set(body) >= {"database_configured", "auth_configured", "allowed_origins"}
        assert not any(isinstance(v, str) and "postgres" in v for v in body.values())


class TestHardening:
    async def test_unknown_key_ids_do_not_refetch_the_jwks_every_time(self, client):
        from tests.authtools import FakeJWKSClient
        calls = {"n": 0}
        original = FakeJWKSClient.get_signing_key_from_jwt

        def counting(self, token):
            calls["n"] += 1
            return original(self, token)
        FakeJWKSClient.get_signing_key_from_jwt = counting
        try:
            for _ in range(5):
                _, token = make_token(kid="rotated-away")
                assert (await client.get("/v1/me", headers=auth(token))).status_code == 401
        finally:
            FakeJWKSClient.get_signing_key_from_jwt = original
        assert calls["n"] == 1                                            # remembered as unknown for a while

    async def test_an_explicitly_unverified_email_is_refused(self, client):
        _, token = make_token(extra={"user_metadata": {"email_verified": False}})
        response = await client.get("/v1/me", headers=auth(token))
        assert response.status_code == 401 and "confirm" in response.json()["error"]["message"]

    def test_production_keeps_the_pilot_gate(self):
        open_gate = Settings(_env_file=None, env="production", require_pilot_membership=False)
        assert any("REQUIRE_PILOT_MEMBERSHIP" in p for p in open_gate.production_problems())
