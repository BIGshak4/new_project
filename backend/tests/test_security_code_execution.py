"""The public answer APIs review source text without ever executing it on the API host.

No real provider, production service, filesystem canary or external command is used.
The indirect-module fixture is stored as text and must never reach even extraction.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api import errors
from app.api.v1 import interviews, practice
from app.engine import checks, code_runner
from app.engine.catalog import load_catalog
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService
from tests.authtools import make_token, make_verifier, member_resolver
from tests.test_practice_hardening import GOOD as EVALUATION
from tests.test_practice_hardening import SEEDS, scripted

SPEC = {"type": "code_tests", "spec": {"language": "python", "entry": ["count_set_bits"],
                                       "cases": [{"args": [3], "expected": 2}]}}
NORMAL = "```python\ndef count_set_bits(x):\n    return bin(x).count('1')\n```"
INDIRECT_MODULE = "```python\nimport dataclasses\ndef count_set_bits(x):\n    return dataclasses.sys.modules['os'].getpid()\n```"


@pytest.fixture
def deny_all_runner_calls(monkeypatch):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("HTTP source must not be parsed or executed by the host runner")

    for name in ("extract_python", "audit", "run_cases", "run_in_subprocess"):
        monkeypatch.setattr(code_runner, name, forbidden)
    return calls


@pytest.mark.parametrize("answer", [NORMAL, INDIRECT_MODULE])
async def test_all_untrusted_dispatch_defaults_fail_closed(answer, deny_all_runner_calls):
    results = [await checks.run_check_async(SPEC, answer), checks.run_check(SPEC, answer),
               checks.check_code_tests(SPEC["spec"], answer)]
    for result in results:
        assert result.type == "code_tests" and result.passed is None
        assert result.detail == checks.CODE_EXECUTION_UNAVAILABLE and result.mismatches == []
    assert not deny_all_runner_calls


def test_trusted_seed_execution_requires_explicit_local_option():
    result = checks.run_check(SPEC, NORMAL, sandbox=False)
    assert result.passed is True and "passes all 1 test cases" in result.detail


@pytest.fixture
async def code_client():
    # First load and validate developer-reviewed seeds, then install a deterministic
    # code-check fixture on a skill present in the normal interview role.
    catalog = load_catalog(SEEDS)
    question = catalog.questions["example-sensor-majority"].model_copy(deep=True,
                 update={"status": "published", "deterministic_check": SPEC})
    catalog.questions = {question.key: question}
    store = InMemoryStore(catalog)
    provider = scripted([EVALUATION])
    app = FastAPI()
    errors.install(app)
    app.include_router(practice.router)
    app.include_router(interviews.router)
    app.state.verifier = make_verifier()
    app.state.access_resolver = member_resolver({"security@example.com"})
    app.state.runtime = SimpleNamespace(
        practice=PracticeService(store, catalog, provider),
        interview=InterviewService(store, catalog, provider, InterviewConfig(reviewed_only=False)))
    _, token = make_token(email="security@example.com")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://security.test") as client:
        yield client, {"Authorization": f"Bearer {token}"}, store, provider


@pytest.mark.parametrize("kind", ["practice", "interview"])
@pytest.mark.parametrize("answer", [NORMAL, INDIRECT_MODULE], ids=["normal-source", "indirect-module-source"])
async def test_network_answers_remain_saved_and_reviewed_without_host_execution(
        code_client, monkeypatch, kind, answer):
    client, headers, store, provider = code_client
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("network source reached a host execution entry point")

    # Patch execution helpers, not the public gate or the evaluator. A regression
    # fails even if the engine catches the raised error and marks evaluation failed.
    for name in ("extract_python", "audit", "run_cases", "run_in_subprocess"):
        monkeypatch.setattr(code_runner, name, forbidden)

    if kind == "practice":
        started = await client.post("/v1/practice/attempts", headers=headers,
                                    json={"question_key": "example-sensor-majority", "mode": "quick"})
        assert started.status_code == 201
        resource_id = started.json()["id"]
        submitted = await client.post(f"/v1/practice/attempts/{resource_id}/submissions", headers=headers,
                                      json={"answer": answer, "idempotency_key": "one"})
        assert submitted.status_code == 200, submitted.text
        saved = submitted.json()["submission"]
        assert saved["answer"] == answer and saved["status"] == "done"
        check = saved["check"]
    else:
        started = await client.post("/v1/interviews", headers=headers, json={"duration_min": 20})
        assert started.status_code == 201, started.text
        resource_id = started.json()["id"]
        submitted = await client.post(f"/v1/interviews/{resource_id}/turns/0/answer", headers=headers,
                                      json={"answer": answer, "idempotency_key": "one"})
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()["turn"]["answer"] == answer
        assert submitted.json()["turn"]["status"] == "done"
        check = store.sessions[uuid.UUID(resource_id)]["turns"][0]["check_result"]
    assert check["passed"] is None and check["detail"] == checks.CODE_EXECUTION_UNAVAILABLE
    assert not calls
    evaluations = [request for request in provider.requests if request.role == "evaluator"]
    assert len(evaluations) == 1
    assert answer in evaluations[0].user
    assert '<check_result type="code_tests" passed="true">' not in evaluations[0].user
