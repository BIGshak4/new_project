"""Night of 31 Oct – 1 Nov 2026: the independent review of Harel's code-execution feature and the avatar/duel services.
Each test is one finding that is now fixed (STATUS §5zw)."""

from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from pathlib import Path

import httpx
import pytest

from app.api.errors import ApiError
from app.config import Settings
from app.engine.catalog import load_catalog
from app.services import code_execution as ce
from app.services.avatars import AvatarsService
from app.services.avatars import load_catalog as load_avatars
from app.services.code_execution import CodeExecutionService, public_key_bytes
from app.services.coins import CoinsService, load_rules
from app.services.duels import load_quiz
from app.services.memory_store import InMemoryStore
from tests.test_practice_hardening import GOOD, SEEDS, attempt_for, scripted

CODE_ANSWER = "Kernighan's loop.\n\n```python\ndef count_set_bits(n):\n    return bin(n).count('1')\n```"


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def runner_with(reply_builder, *, delay: float = 0.0):
    settings = Settings(_env_file=None, seeds_dir=SEEDS, code_execution_signing_seed="fixture-secret-only",
                        code_execution_url="https://executor.test")
    holder = {}

    async def respond(request):
        if request.url.path == "/api/health":
            return httpx.Response(200, json={"available": True, "key_fingerprint":
                                             hashlib.sha256(public_key_bytes(holder["service"].key)).hexdigest()})
        if delay:
            await asyncio.sleep(delay)
        job = json.loads(json.loads(request.content)["job_json"])
        return httpx.Response(200, json=reply_builder(job))
    holder["service"] = CodeExecutionService(settings, transport=httpx.MockTransport(respond))
    return holder["service"]


class TestPracticeSubmitSurvivesTheChecker:
    """Finding 1 (high): the practice engine called the code checker unguarded; a ledger or broker exception left
    the answer EVALUATING for ever. It now falls back to the legacy check and the judge grades the answer as written."""

    async def test_a_raising_checker_does_not_lose_the_answer(self, catalog):
        async def exploding_checker(question, answer, attempt_id):
            raise RuntimeError("relation code_execution_runs does not exist")
        attempt, _ = attempt_for(catalog, scripted([GOOD]), key="example-count-set-bits", code_checker=exploding_checker)
        outcome = await attempt.submit(CODE_ANSWER, idempotency_key="k1")
        assert outcome.band is not None and outcome.submission.status.value == "done"
        assert outcome.check is not None and outcome.check.type == "code_tests" and outcome.check.passed is None

    async def test_a_checker_returning_none_falls_back_the_same_way(self, catalog):
        async def silent_checker(question, answer, attempt_id):
            return None
        attempt, _ = attempt_for(catalog, scripted([GOOD]), key="example-count-set-bits", code_checker=silent_checker)
        outcome = await attempt.submit(CODE_ANSWER, idempotency_key="k1")
        assert outcome.band is not None and outcome.check is not None and outcome.check.passed is None


class TestSubmitPathIsBounded:
    """Finding 2 (medium): the submit path waited up to 58 s on the broker, longer than a judged duel's grace."""

    async def test_a_slow_runner_yields_unavailable_within_the_submit_budget(self, catalog, monkeypatch):
        monkeypatch.setattr(ce, "SUBMIT_EXECUTION_SECONDS", 0.2)
        service = runner_with(lambda job: {}, delay=5.0)
        try:
            started = asyncio.get_running_loop().time()
            check = await service.check_answer(uuid.uuid4(), "duel:x", catalog.questions["example-count-set-bits"], CODE_ANSWER)
            assert asyncio.get_running_loop().time() - started < 2.0
            assert check is not None and check.passed is None and check.execution.status == "unavailable"
            assert "in time" in check.execution.detail
            assert service._health == (0, False)                     # the next call re-probes the broker
        finally:
            await service.aclose()

    async def test_the_run_button_keeps_the_full_client_timeout(self):
        assert ce.SUBMIT_EXECUTION_SECONDS < 58 and ce.SUBMIT_EXECUTION_SECONDS >= 20


class TestStoredExecutionFactsAreTrimmed:
    """Finding 4: the stored copy of a run carried unbounded learner-program output and every hidden test vector."""

    async def test_only_failing_cases_and_bounded_text_are_kept(self, catalog):
        def reply(job):
            cases = [{"index": i, "passed": i != 2, "input": [i], "expected": i, "actual": 99 if i == 2 else i} for i in range(12)]
            return dict(status="failed", language="python", compiled=None, executed=True, passed=False,
                        stdout="x" * 10000, stderr="y" * 10000, compile_output="", runtime_ms=5, cases=cases,
                        test_count=12, passed_count=11, detail="d" * 10000)
        service = runner_with(reply)
        try:
            check = await service.check_answer(uuid.uuid4(), "practice:a", catalog.questions["example-count-set-bits"], CODE_ANSWER)
        finally:
            await service.aclose()
        assert check.passed is False and check.execution.status == "failed"
        assert [c.index for c in check.execution.cases] == [2]                # the hidden passing vectors are not stored
        assert check.execution.test_count == 12 and check.execution.passed_count == 11   # the counts still tell the story
        assert len(check.execution.stdout) == ce.STORED_TEXT_CHARS and len(check.execution.stderr) == ce.STORED_TEXT_CHARS
        assert len(check.execution.detail) == ce.STORED_TEXT_CHARS
        assert check.mismatches == [check.execution.cases[0].model_dump(mode="json")]
        assert len(json.dumps(check.model_dump(mode="json"))) < 20000


class TestAvatarOwnershipAndPrices:
    """Findings 5 and 6: a string price crashed with the wrong error and True passed as a price; a skin dropped from the
    catalog was deleted from the user's paid ownership on their next save."""

    def test_price_validation_names_the_problem(self, tmp_path):
        data = json.loads((SEEDS / "avatar_cosmetics.json").read_text(encoding="utf-8"))
        for bad in ("50", True, -1, None):
            data["skins"][0]["price"] = bad
            path = tmp_path / "c.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with pytest.raises(ValueError, match="price"):
                load_avatars(path)

    async def test_a_paid_skin_survives_its_removal_from_the_catalog(self):
        store = InMemoryStore(load_catalog(SEEDS))
        coins = CoinsService(store, load_rules(SEEDS / "coins.json"))
        full = load_avatars(SEEDS / "avatar_cosmetics.json")
        paid = next(s for s in full["skins"] if s["price"] and s["price"] <= 50)
        user = uuid.uuid4()
        svc = AvatarsService(store, coins, full)
        bought = await svc.buy(user, paid["key"])
        assert paid["key"] in bought["owned_skins"] and bought["balance"] == 50 - paid["price"]
        await svc.save(user, {**bought["avatar"], "skin": paid["key"]})

        trimmed = {**full, "skins": [s for s in full["skins"] if s["key"] != paid["key"]]}
        later = AvatarsService(store, coins, trimmed)
        view = await later.save(user, {**bought["avatar"], "skin": "classic"})
        assert paid["key"] in view["owned_skins"]                         # still owned, just not wearable today
        with pytest.raises(ApiError):
            await later.save(user, {**bought["avatar"], "skin": paid["key"]})   # cannot wear what the catalog lacks

        restored = AvatarsService(store, coins, full)
        again = await restored.buy(user, paid["key"])                     # no second charge
        assert again["balance"] == 50 - paid["price"]
        worn = await restored.save(user, {**bought["avatar"], "skin": paid["key"]})
        assert worn["avatar"]["skin"] == paid["key"]


class TestQuizLoaderRejectsTypos:
    """Finding 7: a misspelt status or a string `correct` silently removed a whole quiz source from production."""

    def test_unknown_status_and_non_integer_correct_are_errors(self, tmp_path):
        good = {"key": "q1", "topic": "t", "status": "approved", "prompt": {"he": "ש", "en": "p"},
                "choices": [{"he": "א", "en": "a"} for _ in range(4)], "correct": 1, "explanation": {"he": "ה", "en": "e"}}
        path = tmp_path / "quiz.json"
        path.write_text(json.dumps({"questions": [good]}), encoding="utf-8")
        assert load_quiz(path)[0].correct == 1
        for field_name, value, message in (("status", "aproved", "status"), ("correct", "1", "integer"), ("correct", True, "integer")):
            path.write_text(json.dumps({"questions": [{**good, field_name: value}]}), encoding="utf-8")
            with pytest.raises(ValueError, match=message):
                load_quiz(path)

    def test_the_shipped_quiz_file_still_loads(self):
        assert len(load_quiz(Path(SEEDS / "duel_quiz.json"))) > 2000


class TestBrokerSurprises:
    """Reviewer findings 6, 8, 10, 11: a non-object health body raised out of the submit path; bodies were size-checked
    after a full download; a broker-side timeout was reused for an hour; the language aliases were never applied."""

    async def test_a_health_body_that_is_not_an_object_means_unavailable_not_a_crash(self, catalog):
        settings = Settings(_env_file=None, seeds_dir=SEEDS, code_execution_signing_seed="fixture-secret-only",
                            code_execution_url="https://executor.test")
        service = CodeExecutionService(settings, transport=httpx.MockTransport(lambda r: httpx.Response(200, json=["ok"])))
        try:
            assert await service.available() is False
            check = await service.check_answer(uuid.uuid4(), "practice:a", catalog.questions["example-count-set-bits"], CODE_ANSWER)
            assert check is not None and check.execution.status == "unavailable"
        finally:
            await service.aclose()

    async def test_an_oversized_reply_is_cut_off_and_treated_as_unavailable(self, catalog):
        def reply(job):
            return dict(status="passed", language="python", compiled=None, executed=True, passed=True, runtime_ms=1,
                        stdout="z" * 200000, cases=[{"index": 0, "passed": True}], detail="")
        service = runner_with(reply)
        try:
            check = await service.check_answer(uuid.uuid4(), "practice:a", catalog.questions["example-count-set-bits"], CODE_ANSWER)
            assert check.passed is None and check.execution.status == "unavailable"
        finally:
            await service.aclose()

    async def test_a_broker_timeout_is_not_reused_for_the_next_submission(self, catalog):
        replies = iter([dict(status="timeout", language="python", compiled=True, executed=True, passed=None, runtime_ms=39000,
                             detail="the program ran past its deadline"),
                        dict(status="passed", language="python", compiled=None, executed=True, passed=True, runtime_ms=5,
                             cases=[{"index": 0, "passed": True}], test_count=1, passed_count=1, detail="1 test passed")])
        service = runner_with(lambda job: next(replies))
        user, question = uuid.uuid4(), catalog.questions["example-count-set-bits"]
        try:
            first = await service.check_answer(user, "practice:a", question, CODE_ANSWER)
            second = await service.check_answer(user, "practice:a", question, CODE_ANSWER)
            assert first.execution.status == "timeout" and first.passed is None
            assert second.execution.status == "passed" and second.passed is True       # the second submit ran again
        finally:
            await service.aclose()

    def test_language_aliases_are_recognised(self):
        from app.services.code_execution import answer_code
        assert answer_code("Loop.\n\n```py\nprint(1)\n```") == ("python", "print(1)")
        assert answer_code("```js\nconsole.log(1)\n```") == ("javascript", "console.log(1)")
        assert answer_code("```c++\nint main(){}\n```") == ("cpp", "int main(){}")
        assert answer_code("```sv\nmodule m; endmodule\n```") == ("systemverilog", "module m; endmodule")
        assert answer_code("```text\nnot code\n```") is None


class TestHealthShowsTheRunner:
    def test_health_reports_wired_and_last_probe_without_calling_the_broker(self):
        from types import SimpleNamespace

        from app.main import _code_execution_health
        assert _code_execution_health(SimpleNamespace(code_execution=None)) is None
        runner = SimpleNamespace(enabled=True, url="https://executor.test", key=object(), _health=(0, False))
        assert _code_execution_health(SimpleNamespace(code_execution=runner)) == {"enabled": True, "wired": True, "last_probe": None}
        runner._health = (10.0, True)
        assert _code_execution_health(SimpleNamespace(code_execution=runner))["last_probe"] == "available"
        runner.key = None
        assert _code_execution_health(SimpleNamespace(code_execution=runner))["wired"] is False
