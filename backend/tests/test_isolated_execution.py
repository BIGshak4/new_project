"""Protocol and API tests. HTTP broker replies are test doubles, not real VM evidence."""

import hashlib
import json
import uuid
from pathlib import Path
from types import SimpleNamespace

import httpx
import jwt
import pytest
from fastapi import FastAPI

from app.api import errors
from app.api.errors import ApiError
from app.api.v1 import practice
from app.config import Settings
from app.engine.catalog import load_catalog
from app.repo.executions import MemoryExecutionLedger
from app.schemas.execution import ExecutionRequest
from app.services.code_execution import CodeExecutionService, answer_code, public_key_bytes
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService
from tests.authtools import make_token, make_verifier, member_resolver
from tests.test_practice_hardening import GOOD, scripted

SEEDS = Path(__file__).resolve().parents[1] / "seeds"


@pytest.fixture
def catalog():
    return load_catalog(SEEDS)


@pytest.fixture
async def runner(catalog):
    state = {"jobs": [], "healthy": True, "reply": None}
    settings = Settings(_env_file=None, seeds_dir=SEEDS, code_execution_signing_seed="fixture-secret-only",
                        code_execution_url="https://executor.test")
    async def respond(request):
        if request.url.path == "/api/health":
            return httpx.Response(200, json={"available": state["healthy"], "key_fingerprint":
                hashlib.sha256(public_key_bytes(service.key)).hexdigest()})
        envelope = json.loads(request.content)
        claims = jwt.decode(envelope["ticket"], service.key.public_key(), algorithms=["EdDSA"], audience="jobrun-executor")
        assert claims["sha256"] == hashlib.sha256(envelope["job_json"].encode()).hexdigest()
        job = json.loads(envelope["job_json"])
        state["jobs"].append(job)
        result = state["reply"] or dict(status="passed", language=job["language"], compiled=None, executed=True,
            passed=True, stdout="", stderr="", compile_output="", runtime_ms=50,
            cases=[{"index": 0, "passed": True, "input": [0], "expected": 0, "actual": 0}],
            detail="1 configured test passed")
        return httpx.Response(200, json=result)
    service = CodeExecutionService(settings, transport=httpx.MockTransport(respond))
    yield service, state
    await service.aclose()


async def test_signs_exact_unicode_source_and_only_server_fixture(runner, catalog):
    service, state = runner
    user = uuid.uuid4()
    question = catalog.questions["example-count-set-bits"]
    request = ExecutionRequest(language="python", source="def count_set_bits(n):\n    # שלום\n    return n.bit_count()",
                               idempotency_key="one")
    result = await service.execute(user, "practice:owned", question, request)
    assert result.passed is True
    job = state["jobs"][0]
    assert "שלום" in job["source"]
    assert job["spec"]["entry"] == "count_set_bits"
    assert "starter" not in job["spec"]
    assert len(job["spec"]["cases"]) > 3
    service._health = (0, False)
    state["healthy"] = False
    replay = await service.execute(user, "practice:owned", question, request)
    assert replay == result and len(state["jobs"]) == 1


async def test_prior_server_run_is_reused_only_for_exact_user_scope_source_and_fixture(runner, catalog):
    service, state = runner
    question, user = catalog.questions["example-count-set-bits"], uuid.uuid4()
    source = "def count_set_bits(n):\n    return n.bit_count()"
    request = ExecutionRequest(language="python", source=source, idempotency_key="one")
    await service.execute(user, "practice:A", question, request)
    check = await service.check_answer(user, "practice:A", question, f"```python\n{source}\n```")
    assert check.passed and check.execution.executed and len(state["jobs"]) == 1
    await service.check_answer(user, "practice:B", question, f"```python\n{source}\n```")
    await service.check_answer(uuid.uuid4(), "practice:A", question, f"```python\n{source}\n```")
    assert len(state["jobs"]) == 3


async def test_mismatched_or_unavailable_broker_never_claims_pass(runner, catalog):
    service, state = runner
    question = catalog.questions["example-count-set-bits"]
    state["healthy"] = False
    result = await service.execute(uuid.uuid4(), "x", question,
        ExecutionRequest(language="python", source="print(1)", idempotency_key="x"))
    assert result.status == "unavailable" and result.passed is None and not state["jobs"]
    state["healthy"] = True
    service._health = (0, False)
    state["reply"] = dict(status="passed", language="python", executed=True, passed=True, cases=[])
    result = await service.execute(uuid.uuid4(), "x", question,
        ExecutionRequest(language="python", source="print(1)", idempotency_key="y"))
    assert result.status == "unavailable" and result.passed is None


async def test_no_suite_cannot_report_correctness(runner, catalog):
    service, state = runner
    question = catalog.questions["example-count-set-bits"]
    state["reply"] = dict(status="completed", language="c", compiled=True, executed=True, passed=None,
                          stdout="3\n", detail="No tests were defined")
    # Use a language without a fixture on this known question copy.
    question = question.model_copy(update={"key": "no-fixture", "deterministic_check": None})
    result = await service.execute(uuid.uuid4(), "x", question,
        ExecutionRequest(language="c", source="int main(void){return 0;}", idempotency_key="x"))
    assert result.status == "completed" and result.passed is None and "spec" not in state["jobs"][0]


async def test_ledger_idempotency_limits_and_concurrent_reservations():
    ledger = MemoryExecutionLedger(daily=10, per_minute=3, concurrent=2)
    user = str(uuid.uuid4())
    one, _ = await ledger.reserve(user, "A", "one", "digest")
    with pytest.raises(ApiError, match="running"):
        await ledger.reserve(user, "A", "one", "digest")
    with pytest.raises(ApiError, match="different"):
        await ledger.reserve(user, "A", "one", "changed")
    two, _ = await ledger.reserve(user, "B", "two", "digest")
    with pytest.raises(ApiError) as busy:
        await ledger.reserve(str(uuid.uuid4()), "C", "three", "digest")
    assert busy.value.status == 429
    await ledger.finish(one, {"status": "completed"})
    _, replay = await ledger.reserve(user, "A", "one", "digest")
    assert replay == {"status": "completed"}
    await ledger.finish(two, {"status": "completed"})
    three, _ = await ledger.reserve(user, "C", "three", "digest")
    await ledger.finish(three, {"status": "completed"})
    with pytest.raises(ApiError) as throttle:
        await ledger.reserve(user, "D", "four", "digest")
    assert throttle.value.status == 429


def test_extraction_never_executes_and_request_forbids_caller_testbench():
    assert answer_code("text ```python\ndef f(): return 1\n``` end") == ("python", "def f(): return 1")
    assert answer_code("a formula") is None
    assert answer_code('Wrong:\n```python\nraise Exception()\n```\n\n````python\ndef f(): return "```"\n````') == ("python", 'def f(): return "```"')
    assert answer_code("```python\nwrong\n```\n\n```text\nformula\n```") is None
    with pytest.raises(ValueError):
        ExecutionRequest(language="python", source="x", idempotency_key="x", spec={"expected": True})


async def test_owned_authenticated_run_then_submit_passes_server_facts_to_ai(runner, catalog):
    service, state = runner
    q = catalog.questions["example-count-set-bits"].model_copy(update={"status": "published"})
    catalog.questions = {q.key: q}
    store = InMemoryStore(catalog)
    provider = scripted([GOOD])
    practice_service = PracticeService(store, catalog, provider)
    practice_service.code_execution = service
    app = FastAPI()
    errors.install(app)
    app.include_router(practice.router)
    app.state.verifier = make_verifier()
    app.state.access_resolver = member_resolver({"runner@example.com", "other@example.com"})
    app.state.runtime = SimpleNamespace(practice=practice_service)
    _, token = make_token(email="runner@example.com")
    _, other = make_token(email="other@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://fixture.test") as client:
        started = await client.post("/v1/practice/attempts", headers=headers, json={"question_key": q.key})
        assert started.status_code == 201, started.text
        attempt_id = started.json()["id"]
        base = f"/v1/practice/attempts/{attempt_id}"
        assert (await client.get(base + "/execution-capabilities")).status_code == 401
        foreign = await client.get(base + "/execution-capabilities", headers={"Authorization": f"Bearer {other}"})
        assert foreign.status_code == 404
        cap = (await client.get(base + "/execution-capabilities", headers=headers)).json()
        assert cap["available"] and "python" in cap["tested_languages"]
        assert "cases" not in json.dumps(cap) and "expected" not in cap
        source = "def count_set_bits(n):\n    return n.bit_count()"
        payload = dict(language="python", source=source, idempotency_key="run1")
        response = await client.post(base + "/executions", headers=headers, json=payload)
        assert response.status_code == 200 and response.json()["passed"] is True
        before = (await client.get(base, headers=headers)).json()
        assert before["submission"] is None
        forbidden = await client.post(base + "/executions", headers=headers, json={**payload, "spec": {}})
        assert forbidden.status_code == 422
        replay = await client.post(base + "/executions", headers=headers, json=payload)
        assert replay.json() == response.json() and len(state["jobs"]) == 1
        submitted = await client.post(base + "/submissions", headers=headers,
            json={"answer": f"Use one-bit counting.\n```python\n{source}\n```", "idempotency_key": "submit1"})
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()["submission"]["check"]["execution"]["status"] == "passed"
        assert len(state["jobs"]) == 1
