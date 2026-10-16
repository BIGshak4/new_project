"""Cross-account isolation at the HTTP boundary using signed local test JWTs."""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api import errors
from app.api.v1 import interviews, practice, questions
from app.engine.catalog import load_catalog
from app.engine.providers import ScriptedProvider
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService
from tests.authtools import make_token, make_verifier, member_resolver
from tests.test_practice_hardening import SEEDS


@pytest.fixture
async def isolated_client():
    catalog = load_catalog(SEEDS)
    store = InMemoryStore(catalog)
    provider = ScriptedProvider([])
    app = FastAPI()
    errors.install(app)
    for router in (practice.router, interviews.router, questions.router):
        app.include_router(router)
    app.state.verifier = make_verifier()
    app.state.access_resolver = member_resolver({"owner@example.com", "other@example.com"})
    app.state.runtime = SimpleNamespace(
        practice=PracticeService(store, catalog, provider),
        interview=InterviewService(store, catalog, provider, InterviewConfig(reviewed_only=False)))
    owner_id, owner_token = make_token(email="owner@example.com")
    other_id, other_token = make_token(email="other@example.com")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://security.test") as client:
        yield client, {"Authorization": f"Bearer {owner_token}"}, {
            "Authorization": f"Bearer {other_token}"}, owner_id, other_id, store, provider


async def test_other_member_cannot_read_mutate_or_reveal_an_attempt(isolated_client, monkeypatch):
    client, owner, other, owner_id, other_id, store, provider = isolated_client
    response = await client.post("/v1/practice/attempts", headers=owner,
                                 json={"question_key": "example-sensor-majority", "user_id": str(other_id)})
    assert response.status_code == 201
    attempt_id = response.json()["id"]
    assert store.attempts[uuid.UUID(attempt_id)]["user_id"] == owner_id
    before = (await client.get(f"/v1/practice/attempts/{attempt_id}", headers=owner)).json()

    requests = [
        ("GET", "", None),
        ("POST", "/hints/next", {}),
        ("POST", "/reference", {}),
        ("POST", "/submissions", {"answer": "other account payload"}),
        ("POST", "/follow-ups/1/submissions", {"answer": "other account payload"}),
        ("POST", "/follow-ups/1/skip", {}),
        ("POST", "/submissions/1/retry", {}),
    ]
    for method, suffix, body in requests:
        denied = await client.request(method, f"/v1/practice/attempts/{attempt_id}{suffix}", headers=other,
                                      **({"json": body} if body is not None else {}))
        assert denied.status_code == 404, (suffix, denied.text)
        assert denied.json()["error"]["code"] == "not_found"
        assert "other account payload" not in denied.text

    async def signing_must_not_be_reached(*args, **kwargs):
        raise AssertionError("foreign attempt must be refused before signing resources")

    monkeypatch.setattr("app.services.question_resources.sign_media", signing_must_not_be_reached)
    denied = await client.get(f"/v1/questions/example-sensor-majority/resources?attempt_id={attempt_id}", headers=other)
    assert denied.status_code == 404
    assert (await client.get(f"/v1/practice/attempts/{attempt_id}", headers=owner)).json() == before
    assert not provider.requests and not store.usage


async def test_other_member_cannot_read_mutate_or_report_an_interview(isolated_client):
    client, owner, other, owner_id, _, store, provider = isolated_client
    response = await client.post("/v1/interviews", headers=owner, json={"duration_min": 20})
    assert response.status_code == 201
    session_id = response.json()["id"]
    assert store.sessions[uuid.UUID(session_id)]["user_id"] == owner_id
    before = (await client.get(f"/v1/interviews/{session_id}", headers=owner)).json()
    for method, suffix, body in [
        ("GET", "", None),
        ("GET", "/report", None),
        ("POST", "/turns/0/answer", {"answer": "other account payload"}),
        ("POST", "/hints/next", {}),
        ("POST", "/end", {}),
    ]:
        denied = await client.request(method, f"/v1/interviews/{session_id}{suffix}", headers=other,
                                      **({"json": body} if body is not None else {}))
        assert denied.status_code == 404, (suffix, denied.text)
        assert denied.json()["error"]["code"] == "not_found"
    assert (await client.get("/v1/interviews", headers=other)).json() == []
    assert (await client.get(f"/v1/interviews/{session_id}", headers=owner)).json() == before
    assert not provider.requests and not store.usage
