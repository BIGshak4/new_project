"""The HTTP contract (integration readiness §6), end to end, offline: in-memory store, scripted model."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.engine.catalog import load_catalog
from app.engine.providers import LLMError
from app.main import app
from app.runtime import build_runtime
from app.services.memory_store import InMemoryStore
from tests.authtools import make_token, make_verifier, member_resolver
from tests.test_practice_hardening import GOOD, SEEDS, WEAK, scripted

MEMBER = "tester@example.com"
Q = "example-sensor-majority"
BASE = "/v1/practice/attempts"


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def runtime_with(catalog, provider, **overrides):
    settings = Settings(_env_file=None, llm_provider="scripted", allow_in_review_content=True, **overrides)
    return build_runtime(settings, catalog=catalog, provider=provider, store=InMemoryStore(catalog))


async def words(client, h, aid, polls: int = 50) -> dict:
    """Poll the attempt like the app does until the grade's words (card, tip, follow-up question) are in."""
    for _ in range(polls):
        view = (await client.get(f"{BASE}/{aid}", headers=h)).json()
        if not view["feedback_pending"]:
            return view
        await asyncio.sleep(0.01)
    raise AssertionError("the feedback never arrived")


@pytest.fixture
async def client(catalog, monkeypatch):
    app.state.verifier = make_verifier()
    app.state.access_resolver = member_resolver({MEMBER, "second@example.com"})
    app.state.runtime = runtime_with(catalog, scripted([WEAK, GOOD, GOOD, GOOD]))
    monkeypatch.setattr(get_settings(), "require_pilot_membership", True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def user():
    user_id, token = make_token(email=MEMBER)
    return user_id, {"Authorization": f"Bearer {token}"}


async def start(client, headers, **body) -> dict:
    response = await client.post(BASE, json={"question_key": Q, **body}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


class TestTheContract:
    @pytest.mark.parametrize("hint_count", [0, 1, 2, 3])
    @pytest.mark.parametrize("reveal_first", [False, True])
    async def test_quick_practice_records_assistance_without_followups(self, client, user, hint_count, reveal_first):
        _, headers = user
        attempt = await start(client, headers, mode="quick", language="he")
        path = f"{BASE}/{attempt['id']}"
        for level in range(1, hint_count + 1):
            hint = (await client.post(path + "/hints/next", headers=headers)).json()
            assert hint["hint"]["level"] == level
        if reveal_first:
            assert (await client.post(path + "/reference", headers=headers)).status_code == 200
        response = await client.post(path + "/submissions", headers={**headers, "Idempotency-Key": "technical-answer"},
                                     json={"answer": {"text": "הסבר של הפתרון\n\n```verilog\nassign alarm = (A & B) | (A & C) | (B & C);\n```"}})
        assert response.status_code == 200
        view = response.json()["attempt"]
        assert view["status"] == "done" and not view["follow_ups"] and view["pending_follow_up"] is None
        assert view["submission"]["hints_seen"] == hint_count
        assert view["submission"]["reference_seen"] is reveal_first
        if reveal_first:
            assert view["submission"]["evidence"] == "none"
        # Revealing afterwards must not retroactively change the accepted answer's assistance.
        await client.post(path + "/reference", headers=headers)
        restored = (await client.get(path, headers=headers)).json()
        assert restored["submission"]["hints_seen"] == hint_count
        assert restored["submission"]["reference_seen"] is reveal_first

    @pytest.mark.parametrize("language", ["he", "en"])
    async def test_grading_requirements_never_leave_question_or_attempt(self, client, user, catalog, language):
        _, headers = user
        # The engine still needs these instructions, but some contain the answer.
        assert catalog.questions[Q].translations[language].requirements
        response = await client.get(f"/v1/questions/{Q}", params={"language": language}, headers=headers)
        assert response.status_code == 200
        assert response.json()["requirements"] == ""
        attempt = await start(client, headers, language=language)
        assert attempt["question"]["requirements"] == ""
        assert attempt["reference"] is None and attempt["hints"] == []
        restored = (await client.get(f"{BASE}/{attempt['id']}", headers=headers)).json()
        assert restored["question"]["requirements"] == ""

    async def test_the_whole_flow_over_http(self, client, user):
        _, h = user
        listing = (await client.get("/v1/questions", params={"language": "he"}, headers=h)).json()
        assert len(listing) == 30 and all(q["language"] == "he" for q in listing)
        assert "reference_solution" not in listing[0] and "hints" not in listing[0]

        detail = (await client.get(f"/v1/questions/{Q}", headers=h)).json()
        assert "alarm" in detail["prompt"].lower() and detail["hint_count"] == 3
        by_id = (await client.get(f"/v1/questions/{detail['id']}", headers=h)).json()
        assert by_id["key"] == Q

        attempt = await start(client, h, mode="deep", language="en", self_confidence=4)
        aid = attempt["id"]
        assert attempt["status"] == "in_progress" and attempt["hints"] == [] and attempt["can_submit"]

        hint = (await client.post(f"{BASE}/{aid}/hints/next", headers=h)).json()
        assert hint["hint"]["level"] == 1 and hint["attempt"]["hints_remaining"] == 2

        response = await client.post(f"{BASE}/{aid}/submissions", json={"answer": {"text": "alarm = A ^ B ^ C"}},
                                     headers={**h, "Idempotency-Key": "k1"})
        assert response.status_code == 200, response.text
        body = response.json()
        sub = body["submission"]
        assert sub["status"] == "done" and sub["band"] == "WEAK" and sub["check"]["passed"] is False
        # grade first: the result is complete, its words follow (the app polls)
        assert sub["feedback_pending"] and sub["card"] is None and sub["xp_earned"] and sub["key"] == "k1"
        assert body["attempt"]["pending_follow_up"]["turn"] == 1 and not body["attempt"]["can_submit"]
        assert body["attempt"]["pending_follow_up"]["question_pending"] and body["attempt"]["feedback_pending"]
        assert "evaluation" not in sub and "evidence_weight" not in sub          # internals never leave

        view = await words(client, h, aid)
        sub = view["submission"]
        assert sub["card"]["next_step"] and sub["tip"]["key"] and sub["follow_up"] and not sub["feedback_pending"]
        assert view["pending_follow_up"]["question"] == sub["follow_up"]
        while view["pending_follow_up"] is not None:
            turn = view["pending_follow_up"]["turn"]
            response = await client.post(f"{BASE}/{aid}/follow-ups/{turn}/submissions",
                                         json={"answer": "majority means at least two of three"}, headers=h)
            assert response.status_code == 200, response.text
            view = await words(client, h, aid)
        assert view["status"] == "done"

        again = (await client.get(f"{BASE}/{aid}", headers=h)).json()
        assert again["submission"]["card"] == sub["card"] and len(again["hints"]) >= 1     # the WEAK answer added a level-2 hint

        progress = (await client.get("/v1/me/progress", headers=h)).json()
        assert progress["attempts_today"] == 1 and progress["skills"] and progress["recent"][0]["question_key"] == Q
        assert {"key", "label", "level", "status", "trend"} <= set(progress["skills"][0])

    async def test_idempotency_over_http(self, client, user):
        _, h = user
        aid = (await start(client, h))["id"]
        first = await client.post(f"{BASE}/{aid}/submissions", json={"answer": "alarm = A ^ B ^ C"},
                                  headers={**h, "Idempotency-Key": "same"})
        second = await client.post(f"{BASE}/{aid}/submissions", json={"answer": "alarm = A ^ B ^ C"},
                                   headers={**h, "Idempotency-Key": "same"})
        assert second.status_code == 200 and second.json()["submission"]["replayed"] is True
        assert second.json()["submission"]["band"] == first.json()["submission"]["band"]
        settled = await words(client, h, aid)
        third = await client.post(f"{BASE}/{aid}/submissions", json={"answer": "alarm = A ^ B ^ C"},
                                  headers={**h, "Idempotency-Key": "same"})
        assert third.json()["submission"]["card"] == settled["submission"]["card"] is not None

        conflict = await client.post(f"{BASE}/{aid}/submissions", json={"answer": "something else"},
                                     headers={**h, "Idempotency-Key": "same"})
        assert conflict.status_code == 409 and conflict.json()["error"]["code"] == "conflict"

        again = await client.post(f"{BASE}/{aid}/submissions", json={"answer": "a new answer"}, headers=h)
        assert again.status_code == 409 and again.json()["error"]["code"] == "already_submitted"

    async def test_a_generated_key_is_returned_for_reuse(self, client, user):
        _, h = user
        aid = (await start(client, h))["id"]
        response = await client.post(f"{BASE}/{aid}/submissions", json={"answer": "alarm = A ^ B ^ C"}, headers=h)
        key = response.json()["submission"]["key"]
        assert uuid.UUID(key)
        replay = await client.post(f"{BASE}/{aid}/submissions", json={"answer": "alarm = A ^ B ^ C", "idempotency_key": key},
                                   headers=h)
        assert replay.json()["submission"]["replayed"] is True

    async def test_reveal_then_answer(self, client, user):
        _, h = user
        aid = (await start(client, h))["id"]
        revealed = (await client.post(f"{BASE}/{aid}/reference", headers=h)).json()
        assert revealed["reference"] and revealed["attempt"]["reference"] == revealed["reference"]
        response = await client.post(f"{BASE}/{aid}/submissions", json={"answer": "alarm = (A&B)|(A&C)|(B&C)"}, headers=h)
        assert response.json()["submission"]["evidence"] == "none"


class TestErrors:
    async def test_model_outage_then_retry(self, client, user, catalog):
        app.state.runtime = runtime_with(catalog, scripted([LLMError("down", retryable=False), GOOD]))
        _, h = user
        aid = (await start(client, h))["id"]
        response = await client.post(f"{BASE}/{aid}/submissions", json={"answer": "alarm = A ^ B ^ C"}, headers=h)
        assert response.status_code == 200 and response.json()["submission"]["status"] == "failed"
        assert response.json()["attempt"]["can_retry"]

        wrong = await client.post(f"{BASE}/{aid}/submissions/7/retry", headers=h)
        assert wrong.status_code == 409 and wrong.json()["error"]["code"] == "nothing_to_retry"
        retried = await client.post(f"{BASE}/{aid}/submissions/1/retry", headers=h)
        assert retried.status_code == 200 and retried.json()["submission"]["status"] == "done"
        nothing = await client.post(f"{BASE}/{aid}/submissions/1/retry", headers=h)
        assert nothing.status_code == 409

    @pytest.mark.parametrize("body, code", [
        ({}, "validation"),
        ({"question_key": "nope"}, "not_found"),
        ({"question_key": Q, "mode": "simulation"}, "validation"),
        ({"question_key": Q, "language": "fr"}, "validation"),
        ({"question_key": Q, "self_confidence": 9}, "validation"),
    ])
    async def test_bad_starts(self, client, user, body, code):
        _, h = user
        response = await client.post(BASE, json=body, headers=h)
        assert response.status_code in (404, 422) and response.json()["error"]["code"] == code

    @pytest.mark.parametrize("body", [{"answer": ""}, {"answer": "   "}, {"answer": "x" * 20_001},
                                      {"answer": {"text": "x" * 20_001}}, {"answer": 5}, {"nope": 1}])
    async def test_bad_answers_are_422_never_500(self, client, user, body):
        _, h = user
        aid = (await start(client, h))["id"]
        response = await client.post(f"{BASE}/{aid}/submissions", json=body, headers=h)
        assert response.status_code == 422 and response.json()["error"]["code"] == "validation"

    async def test_malformed_json_is_422(self, client, user):
        _, h = user
        aid = (await start(client, h))["id"]
        response = await client.post(f"{BASE}/{aid}/submissions", content=b"{not json", headers={**h, "Content-Type": "application/json"})
        assert response.status_code == 422

    async def test_wrong_follow_up_turn(self, client, user):
        _, h = user
        aid = (await start(client, h))["id"]
        await client.post(f"{BASE}/{aid}/submissions", json={"answer": "alarm = A ^ B ^ C"}, headers=h)
        response = await client.post(f"{BASE}/{aid}/follow-ups/3/submissions", json={"answer": "x"}, headers=h)
        assert response.status_code == 409 and response.json()["error"]["code"] == "no_pending_follow_up"

    async def test_daily_limit_is_429(self, client, user, catalog):
        app.state.runtime = runtime_with(catalog, scripted([GOOD]), daily_attempt_limit=1)
        _, h = user
        await start(client, h)
        response = await client.post(BASE, json={"question_key": Q}, headers=h)
        assert response.status_code == 429 and response.json()["error"]["code"] == "usage_limit"

    async def test_unknown_paths_and_methods_use_the_error_shape(self, client, user):
        _, h = user
        response = await client.get("/v1/nothing-here", headers=h)
        assert response.status_code == 404 and response.json()["error"]["code"] == "not_found"
        response = await client.delete(f"{BASE}/{uuid.uuid4()}", headers=h)
        assert response.status_code == 405 and response.json()["error"]["code"] == "method_not_allowed"

    async def test_oversized_bodies_are_413_before_parsing(self, client, user):
        _, h = user
        aid = (await start(client, h))["id"]
        response = await client.post(f"{BASE}/{aid}/submissions", content=b"x" * (300 * 1024),
                                     headers={**h, "Content-Type": "application/json"})
        assert response.status_code == 413 and response.json()["error"]["code"] == "payload_too_large"

    async def test_hebrew_survives_the_wire(self, client, user):
        _, h = user
        attempt = await start(client, h, language="he")
        assert any("֐" <= ch <= "׿" for ch in attempt["question"]["prompt"])
        hint = (await client.post(f"{BASE}/{attempt['id']}/hints/next", headers=h))
        assert hint.status_code == 200
        assert any("֐" <= ch <= "׿" for ch in hint.json()["hint"]["text"])

    async def test_unknown_attempt_and_bad_ids(self, client, user):
        _, h = user
        assert (await client.get(f"{BASE}/{uuid.uuid4()}", headers=h)).status_code == 404
        assert (await client.get(f"{BASE}/not-a-uuid", headers=h)).status_code == 422

    async def test_an_unexpected_error_is_a_500_with_a_request_id_not_a_traceback(self, client, user, catalog):
        from app.engine.providers import ScriptedProvider

        def explode(request):
            raise RuntimeError("boom")
        app.state.runtime = runtime_with(catalog, ScriptedProvider(explode))
        _, h = user
        aid = (await start(client, h))["id"]
        response = await client.post(f"{BASE}/{aid}/submissions", json={"answer": "alarm = A ^ B ^ C"},
                                     headers={**h, "X-Request-Id": "req-42"})
        assert response.status_code == 500 and response.headers["x-request-id"] == "req-42"
        assert response.json()["error"]["code"] == "internal" and "boom" not in response.text


def every_route():
    aid = str(uuid.uuid4())
    return [
        ("GET", "/v1/me", None), ("GET", "/v1/me/progress", None), ("GET", "/v1/questions", None),
        ("GET", f"/v1/questions/{Q}", None), ("POST", BASE, {"question_key": Q}), ("GET", f"{BASE}/{aid}", None),
        ("POST", f"{BASE}/{aid}/hints/next", None), ("POST", f"{BASE}/{aid}/reference", None),
        ("POST", f"{BASE}/{aid}/submissions", {"answer": "x"}), ("POST", f"{BASE}/{aid}/follow-ups/1/submissions", {"answer": "x"}),
        ("POST", f"{BASE}/{aid}/submissions/1/retry", None),
        # mock interviews
        ("POST", "/v1/interviews", {"duration_min": 20}), ("GET", "/v1/interviews", None),
        ("GET", f"/v1/interviews/{aid}", None), ("POST", f"/v1/interviews/{aid}/turns/0/answer", {"answer": "x"}),
        ("POST", f"/v1/interviews/{aid}/hints/next", None), ("POST", f"/v1/interviews/{aid}/end", None),
        ("GET", f"/v1/interviews/{aid}/report", None),
        # goal, job types, company sightings
        ("GET", "/v1/me/goal", None), ("POST", "/v1/me/goal", {"job_type": "verification", "minutes_per_day": 30}),
        ("GET", "/v1/job-types", None), ("GET", "/v1/companies", None),
        ("POST", f"/v1/questions/{Q}/sightings", {"company": "Intel"}),
        ("GET", "/v1/me/program", None), ("POST", "/v1/me/program/start", {}),
    ]


class TestEveryRouteIsProtected:
    @pytest.mark.parametrize("method, path, body", every_route(), ids=lambda v: v if isinstance(v, str) and v.startswith("/") else "")
    async def test_no_token_401(self, client, method, path, body):
        response = await client.request(method, path, json=body)
        assert response.status_code == 401 and response.json()["error"]["code"] == "unauthenticated"

    @pytest.mark.parametrize("method, path, body", every_route(), ids=lambda v: v if isinstance(v, str) and v.startswith("/") else "")
    async def test_non_member_403(self, client, method, path, body):
        _, token = make_token(email="stranger@example.com")
        response = await client.request(method, path, json=body, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403 and response.json()["error"]["code"] == "forbidden"

    async def test_every_v1_route_in_the_openapi_document_is_covered(self, client):
        spec = (await client.get("/openapi.json")).json()
        v1 = {(m.upper(), p) for p, ops in spec["paths"].items() if p.startswith("/v1") for m in ops}
        covered = {(m, p.replace(str(uuid.UUID(int=0)), "{attempt_id}")) for m, p, _ in every_route()}
        normalized = set()
        for m, p in covered:
            parts = [("{attempt_id}" if _is_uuid(x) else x) for x in p.split("/")]
            normalized.add((m, "/".join(parts)))
        normalized = {(m, p.replace(f"/{Q}", "/{key_or_id}").replace("/follow-ups/1/", "/follow-ups/{turn}/")
                       .replace("/submissions/1/retry", "/submissions/{revision}/retry")) for m, p in normalized}
        normalized = {(m, p.replace("/v1/interviews/{attempt_id}", "/v1/interviews/{interview_id}")
                       .replace("/turns/0/answer", "/turns/{turn_index}/answer")) for m, p in normalized}
        assert v1 == normalized, f"routes without a protection test: {v1 - normalized}"

    async def test_another_users_attempt_is_404_on_every_route(self, client, user):
        _, h = user
        aid = (await start(client, h))["id"]
        _, other = make_token(email="second@example.com")
        oh = {"Authorization": f"Bearer {other}"}
        for method, path, body in [("GET", f"{BASE}/{aid}", None), ("POST", f"{BASE}/{aid}/hints/next", None),
                                   ("POST", f"{BASE}/{aid}/reference", None), ("POST", f"{BASE}/{aid}/submissions", {"answer": "x"}),
                                   ("POST", f"{BASE}/{aid}/follow-ups/1/submissions", {"answer": "x"}),
                                   ("POST", f"{BASE}/{aid}/submissions/1/retry", None)]:
            response = await client.request(method, path, json=body, headers=oh)
            assert response.status_code == 404, (path, response.text)


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


class TestOpenApi:
    async def test_the_contract_is_documented(self, client):
        spec = (await client.get("/openapi.json")).json()
        submit = spec["paths"][f"{BASE}/{{attempt_id}}/submissions"]["post"]
        assert any(p["name"] == "Idempotency-Key" for p in submit["parameters"])
        assert {"200", "409", "503", "422"} <= set(submit["responses"])
        schemas = spec["components"]["schemas"]
        assert "AttemptView" in schemas and "SubmissionView" in schemas and "ProgressView" in schemas
        assert "evaluation" not in schemas["SubmissionView"]["properties"]


class TestSlowEvaluations:
    async def test_a_slow_evaluation_answers_202_and_finishes_in_the_background(self, client, user, catalog, monkeypatch):
        import asyncio as _asyncio

        from app.api.v1 import practice as practice_routes
        from app.engine.providers import ScriptedProvider

        class Slow(ScriptedProvider):
            async def complete(self, request):
                if request.role == "evaluator":
                    await _asyncio.sleep(0.6)
                return await super().complete(request)

        app.state.runtime = runtime_with(catalog, Slow(lambda r: {"evaluator": GOOD, "generator": {
            "question_text": "follow?", "question_archetype": "design", "expected_answer_outline": "x", "rubric_focus": []},
            "feedback": {"what_happened": "w", "why_it_matters": "y", "next_step": "n", "your_reasoning_vs_reference": "c"},
            "tip": "t"}[r.role]))
        monkeypatch.setattr(practice_routes, "RESPONSE_BUDGET_SECONDS", 0.2)
        _, h = user
        aid = (await start(client, h))["id"]
        response = await client.post(f"{BASE}/{aid}/submissions", json={"answer": "alarm = (A&B)|(A&C)|(B&C)"},
                                     headers={**h, "Idempotency-Key": "slow-1"})
        assert response.status_code == 202, response.text
        body = response.json()
        assert body["submission"]["status"] == "evaluating" and body["attempt"]["status"] == "evaluating"
        assert not body["attempt"]["can_retry"] and not body["attempt"]["can_submit"]

        retry = await client.post(f"{BASE}/{aid}/submissions/1/retry", headers=h)
        assert retry.status_code == 409                                  # nothing to retry while it runs

        for _ in range(30):                                              # the client polls
            view = (await client.get(f"{BASE}/{aid}", headers=h)).json()
            if view["status"] != "evaluating":
                break
            await _asyncio.sleep(0.1)
        assert view["submission"]["status"] == "done" and view["submission"]["band"] == "STRONG"
        replay = await client.post(f"{BASE}/{aid}/submissions", json={"answer": "alarm = (A&B)|(A&C)|(B&C)"},
                                   headers={**h, "Idempotency-Key": "slow-1"})
        assert replay.status_code == 200 and replay.json()["submission"]["replayed"] is True


class TestDroppedDatabaseConnections:
    async def test_a_dropped_connection_is_a_503_with_retry_after(self, client, user, catalog):
        from sqlalchemy.exc import DBAPIError

        from app.services import memory_store

        async def dropped(self, *a, **k):
            raise DBAPIError("SELECT 1", {}, ConnectionResetError(10054, "forcibly closed"), connection_invalidated=True)
        _, h = user
        aid = (await start(client, h))["id"]
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(memory_store._MemoryTx, "load_attempt", dropped)
        try:
            response = await client.get(f"{BASE}/{aid}", headers=h)
        finally:
            monkeypatch.undo()
        assert response.status_code == 503 and response.json()["error"]["code"] == "temporarily_unavailable"
        assert response.headers.get("retry-after") == "2"

    async def test_a_single_drop_during_load_is_retried_transparently(self, client, user, catalog):
        from sqlalchemy.exc import DBAPIError

        from app.services import memory_store
        original = memory_store._MemoryTx.load_attempt
        calls = {"n": 0}

        async def flaky(self, *a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                raise DBAPIError("SELECT 1", {}, ConnectionResetError(10054, "forcibly closed"), connection_invalidated=True)
            return await original(self, *a, **k)
        _, h = user
        aid = (await start(client, h))["id"]
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(memory_store._MemoryTx, "load_attempt", flaky)
        try:
            response = await client.get(f"{BASE}/{aid}", headers=h)
        finally:
            monkeypatch.undo()
        assert response.status_code == 200 and calls["n"] == 2

    async def test_a_real_query_error_is_still_a_500(self, client, user, catalog):
        from sqlalchemy.exc import DBAPIError

        from app.services import memory_store

        async def broken(self, *a, **k):
            raise DBAPIError("SELECT nope", {}, Exception("column nope does not exist"))
        _, h = user
        aid = (await start(client, h))["id"]
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(memory_store._MemoryTx, "load_attempt", broken)
        try:
            response = await client.get(f"{BASE}/{aid}", headers=h)
        finally:
            monkeypatch.undo()
        assert response.status_code == 500 and response.json()["error"]["code"] == "internal"


class TestProvenance:
    async def test_scripted_results_are_marked_demo_and_carry_no_model(self, client, user):
        _, h = user
        aid = (await start(client, h))["id"]
        body = (await client.post(f"{BASE}/{aid}/submissions", json={"answer": "alarm = A ^ B ^ C"}, headers=h)).json()
        assert body["submission"]["assessed_by"] == "demo" and body["submission"]["model"] is None
        again = (await client.get(f"{BASE}/{aid}", headers=h)).json()
        assert again["submission"]["assessed_by"] == "demo"

    async def test_a_real_model_result_is_marked_model(self, client, user, catalog):
        from tests.test_practice_hardening import scripted
        app.state.runtime = runtime_with(catalog, scripted([GOOD], metered=True))      # reports claude-opus-5
        _, h = user
        aid = (await start(client, h))["id"]
        body = (await client.post(f"{BASE}/{aid}/submissions", json={"answer": "alarm = (A&B)|(A&C)|(B&C)"}, headers=h)).json()
        assert body["submission"]["assessed_by"] == "model" and body["submission"]["model"] == "claude-opus-5"
