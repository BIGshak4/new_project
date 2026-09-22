"""The mock-interview HTTP contract, offline: in-memory store, scripted model."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.engine.catalog import load_catalog
from app.engine.providers import ScriptedProvider
from app.main import app
from app.runtime import build_runtime
from app.services.memory_store import InMemoryStore
from tests.authtools import make_token, make_verifier, member_resolver
from tests.test_practice_hardening import GOOD, SEEDS, WEAK

MEMBER = "tester@example.com"
BASE = "/v1/interviews"


def provider():
    replies = [GOOD, WEAK]
    n = {"i": 0}

    def respond(request):
        if request.role == "evaluator":
            n["i"] += 1
            return replies[n["i"] % 2]
        return "## Summary\nfine" if request.role == "report" else "unused"
    return ScriptedProvider(respond)


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


@pytest.fixture
async def client(catalog, monkeypatch):
    settings = Settings(_env_file=None, llm_provider="scripted", allow_in_review_content=True,
                        interview_reviewed_only=False, interview_daily_limit=3)
    app.state.verifier = make_verifier()
    app.state.access_resolver = member_resolver({MEMBER})
    app.state.runtime = build_runtime(settings, catalog=catalog, provider=provider(), store=InMemoryStore(catalog))
    monkeypatch.setattr(get_settings(), "require_pilot_membership", True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def headers():
    _, token = make_token(email=MEMBER)
    return {"Authorization": f"Bearer {token}"}


async def test_start_answer_hint_end_report(client, headers):
    response = await client.post(BASE, json={"duration_min": 30, "language": "en"}, headers=headers)
    assert response.status_code == 201, response.text
    interview = response.json()
    assert interview["status"] == "in_progress" and interview["current_turn"]["index"] == 0
    assert interview["current_turn"]["band"] is None and interview["results_revealed"] is False
    path = f"{BASE}/{interview['id']}"

    listed = (await client.get(BASE, headers=headers)).json()
    assert listed[0]["id"] == interview["id"] and listed[0]["status"] == "in_progress"

    if interview["can_hint"]:
        hinted = (await client.post(path + "/hints/next", headers=headers)).json()
        assert hinted["hint"]["level"] == 1 and hinted["interview"]["hints_used"] == 1

    answered = await client.post(path + "/turns/0/answer", headers={**headers, "Idempotency-Key": "a0"},
                                 json={"answer": "alarm = AB + BC + AC, at least two of three"})
    assert answered.status_code == 200, answered.text
    body = answered.json()
    assert body["turn"]["status"] == "done" and body["turn"]["band"] is None       # hidden mid-interview
    assert body["interview"]["current_turn"]["index"] == 1

    replay = await client.post(path + "/turns/0/answer", headers={**headers, "Idempotency-Key": "a0"},
                               json={"answer": "alarm = AB + BC + AC, at least two of three"})
    assert replay.status_code == 200 and replay.json()["turn"]["index"] == 0
    conflict = await client.post(path + "/turns/0/answer", headers={**headers, "Idempotency-Key": "other"},
                                 json={"answer": "something else"})
    assert conflict.status_code == 409 and conflict.json()["error"]["code"] == "already_submitted"

    too_early = await client.get(path + "/report", headers=headers)
    assert too_early.status_code == 409

    ended = (await client.post(path + "/end", headers=headers)).json()
    assert ended["status"] == "completed" and ended["ended_early"] and ended["report_ready"]
    assert ended["turns"][0]["band"] in ("STRONG", "PARTIAL", "WEAK")                  # revealed now

    report = await client.get(path + "/report", headers=headers)
    assert report.status_code == 200, report.text
    data = report.json()
    assert data["session_id"] == interview["id"] and "session_overall" in data["fit"]
    # the scripted runtime writes the plain report (no model narrative); the real provider fills narrative_source=generated
    assert data["narrative_md"].startswith("## Summary") and data["narrative_source"] == "fallback"
    assert data["turns"][0]["band"] is not None and data["skills"]

    restored = (await client.get(path, headers=headers)).json()
    assert restored["status"] == "completed" and restored["current_turn"] is None


async def test_validation_limits_and_auth(client, headers):
    assert (await client.post(BASE, json={"duration_min": 25})).status_code == 401
    bad = await client.post(BASE, json={"duration_min": 25}, headers=headers)
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "validation"
    for _ in range(3):
        assert (await client.post(BASE, json={"duration_min": 20}, headers=headers)).status_code == 201
    limited = await client.post(BASE, json={"duration_min": 20}, headers=headers)
    assert limited.status_code == 429 and limited.json()["error"]["code"] == "usage_limit"
    missing = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000", headers=headers)
    assert missing.status_code == 404


async def test_reviewed_only_refuses_when_nothing_is_published(catalog, monkeypatch):
    settings = Settings(_env_file=None, llm_provider="scripted", allow_in_review_content=True)   # interview_reviewed_only=True
    app.state.verifier = make_verifier()
    app.state.access_resolver = member_resolver({MEMBER})
    app.state.runtime = build_runtime(settings, catalog=catalog, provider=provider(), store=InMemoryStore(catalog))
    monkeypatch.setattr(get_settings(), "require_pilot_membership", True)
    _, token = make_token(email=MEMBER)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        response = await c.post(BASE, json={"duration_min": 20}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 409 and response.json()["error"]["code"] == "no_reviewed_questions"
