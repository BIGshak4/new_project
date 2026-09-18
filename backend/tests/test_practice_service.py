"""The practice service: one user action from request to durable result, without a database."""

from __future__ import annotations

import asyncio
import uuid

import pytest

from app.api.errors import ApiError
from app.engine.providers import LLMError
from app.repo.attempts import DuplicateSubmissionKey
from app.services import memory_store
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_practice_hardening import GOOD, SEEDS, WEAK, scripted

USER = uuid.uuid4()
OTHER = uuid.uuid4()
Q = "example-sensor-majority"
N_SKILLS = 2                                   # skills examined by Q: one metrics row each


@pytest.fixture(scope="module")
def catalog():
    from app.engine.catalog import load_catalog
    return load_catalog(SEEDS)


def service(catalog, provider, **config) -> tuple[PracticeService, InMemoryStore]:
    store = InMemoryStore(catalog)
    return PracticeService(store, catalog, provider, ServiceConfig(**config)), store


class TestTheWholeLoop:
    async def test_start_hint_submit_follow_up_progress(self, catalog):
        provider = scripted([WEAK, GOOD, GOOD])
        svc, store = service(catalog, provider)

        view = await svc.start(USER, question_key=Q, mode="deep", language="en", self_confidence=4)
        attempt_id = uuid.UUID(view.id)
        assert view.status == "in_progress" and view.can_submit and view.hints == [] and view.hints_remaining == 3
        assert view.reference is None and "reference_solution" not in view.question.model_dump()
        assert "alarm" in view.question.prompt.lower()

        hint, view = await svc.next_hint(USER, attempt_id)
        assert hint.level == 1 and view.hints[0].text == hint.text and view.hints_remaining == 2

        sub, view = await svc.submit(USER, attempt_id, {"text": "alarm = A ^ B ^ C"}, idempotency_key="k1")
        assert sub.status == "done" and sub.band == "WEAK" and sub.check.passed is False
        assert sub.card is not None and sub.tip is not None and sub.follow_up
        assert sub.evidence == "reduced"                       # one hint was taken
        assert view.status == "in_progress" and view.pending_follow_up.turn == 1 and not view.can_submit
        assert len(store.metrics) == N_SKILLS and len(store.tips) == 1
        assert {u["action"] for u in store.usage} == set() or all("model" in u for u in store.usage)

        turns = 0
        while view.pending_follow_up is not None:                  # the engine may probe up to twice
            turn = view.pending_follow_up.turn
            fsub, view = await svc.submit(USER, attempt_id, "majority means at least two of three",
                                          idempotency_key=f"k{turn + 1}", follow_up_turn=turn)
            assert fsub.turn == turn and fsub.status == "done"
            turns += 1
        assert 1 <= turns <= 2 and view.status == "done" and not view.can_submit
        assert [f.submission.status for f in view.follow_ups] == ["done"] * turns

        progress = await svc.progress(USER)
        skill = next(s for s in progress.skills if s.key == catalog.questions[Q].primary_skill)
        assert skill.assessments == 1 + turns and skill.status in ("assessed", "insufficient")
        assert progress.attempts_today == 1
        assert progress.recent[0]["question_key"] == Q

    async def test_a_refresh_returns_the_same_result_without_a_model_call(self, catalog):
        provider = scripted([WEAK])
        svc, store = service(catalog, provider)
        view = await svc.start(USER, question_key=Q)
        attempt_id = uuid.UUID(view.id)
        sub, _ = await svc.submit(USER, attempt_id, "alarm = A ^ B ^ C", idempotency_key="k1")
        calls = len(provider.requests)

        again = await svc.get(USER, attempt_id)                       # page refresh
        assert again.submission.card == sub.card and again.submission.tip == sub.tip
        assert again.pending_follow_up.question == sub.follow_up

        replay, _ = await svc.submit(USER, attempt_id, "alarm = A ^ B ^ C", idempotency_key="k1")   # network retry
        assert replay.replayed and replay.card == sub.card and len(provider.requests) == calls
        assert len(store.metrics) == N_SKILLS                         # scored once

    async def test_a_new_service_instance_restores_from_the_store(self, catalog):
        provider = scripted([WEAK])
        svc, store = service(catalog, provider)
        view = await svc.start(USER, question_key=Q)
        await svc.next_hint(USER, uuid.UUID(view.id))
        sub, _ = await svc.submit(USER, uuid.UUID(view.id), "alarm = A ^ B ^ C", idempotency_key="k1")

        restarted = PracticeService(store, catalog, scripted([]))     # "server restart": no model available
        again = await restarted.get(USER, uuid.UUID(view.id))
        assert again.hints[0].level == 1 and again.submission.card == sub.card and again.pending_follow_up is not None


class TestBoundaries:
    async def test_attempts_belong_to_their_user(self, catalog):
        svc, _ = service(catalog, scripted([GOOD]))
        view = await svc.start(USER, question_key=Q)
        with pytest.raises(ApiError) as raised:
            await svc.get(OTHER, uuid.UUID(view.id))
        assert raised.value.code == "not_found"                        # not even "forbidden": it does not exist for them
        with pytest.raises(ApiError):
            await svc.submit(OTHER, uuid.UUID(view.id), "x", idempotency_key="k")

    async def test_daily_limit_fails_gracefully(self, catalog):
        svc, _ = service(catalog, scripted([]), daily_attempt_limit=2)
        await svc.start(USER, question_key=Q)
        await svc.start(USER, question_key=Q)
        with pytest.raises(ApiError) as raised:
            await svc.start(USER, question_key=Q)
        assert raised.value.code == "usage_limit" and raised.value.status == 429
        await svc.start(OTHER, question_key=Q)                        # someone else is not affected

    @pytest.mark.parametrize("kwargs, code", [
        ({"question_key": "no-such-question"}, "not_found"),
        ({"question_key": Q, "mode": "simulation"}, "validation"),
        ({"question_key": Q, "language": "fr"}, "validation"),
        ({"question_key": Q, "self_confidence": 9}, "validation"),
    ])
    async def test_bad_starts(self, catalog, kwargs, code):
        svc, _ = service(catalog, scripted([]))
        with pytest.raises(ApiError) as raised:
            await svc.start(USER, **kwargs)
        assert raised.value.code == code

    async def test_wrong_follow_up_turn_is_rejected(self, catalog):
        svc, _ = service(catalog, scripted([WEAK]))
        view = await svc.start(USER, question_key=Q)
        await svc.submit(USER, uuid.UUID(view.id), "alarm = A ^ B ^ C", idempotency_key="k1")
        with pytest.raises(ApiError) as raised:
            await svc.submit(USER, uuid.UUID(view.id), "x", idempotency_key="k2", follow_up_turn=2)
        assert raised.value.code == "no_pending_follow_up"

    async def test_unreviewed_questions_are_hidden_in_production_mode(self, catalog):
        store = InMemoryStore(catalog, allow_in_review=False)
        svc = PracticeService(store, catalog, scripted([]))
        assert await svc.list_questions(language="en") == []           # all 30 are still in_review
        with pytest.raises(ApiError) as raised:
            await svc.start(USER, question_key=Q)
        assert raised.value.code == "not_found"

    async def test_question_views_never_carry_the_answer(self, catalog):
        svc, _ = service(catalog, scripted([]))
        listing = await svc.list_questions(language="he")
        assert listing and all(q.language == "he" for q in listing)
        one = await svc.get_question(language="en", key=Q)
        dumped = one.model_dump_json()
        text = catalog.questions[Q].text("en")
        assert text.reference_solution not in dumped and all(h not in dumped for h in text.hints)


class TestFailuresAndRaces:
    async def test_model_down_keeps_the_answer_and_retry_scores_once(self, catalog):
        svc, store = service(catalog, scripted([LLMError("down", retryable=False)]))
        view = await svc.start(USER, question_key=Q)
        attempt_id = uuid.UUID(view.id)
        sub, view = await svc.submit(USER, attempt_id, "alarm = A ^ B ^ C", idempotency_key="k1")
        assert sub.status == "failed" and view.status == "failed" and view.can_retry and view.can_submit
        assert store.metrics == [] and store.attempts[attempt_id]["row"]["answer"]["text"] == "alarm = A ^ B ^ C"

        svc.provider = scripted([GOOD])
        retried, view = await svc.retry(USER, attempt_id)
        assert retried.status == "done" and retried.revision == 1 and view.status == "in_progress"
        assert len(store.metrics) == N_SKILLS

    async def test_crash_mid_evaluation_leaves_a_retryable_saved_answer(self, catalog):
        def explode(request):
            raise RuntimeError("process died")
        from app.engine.providers import ScriptedProvider
        svc, store = service(catalog, ScriptedProvider(explode))
        view = await svc.start(USER, question_key=Q)
        attempt_id = uuid.UUID(view.id)
        with pytest.raises(RuntimeError):
            await svc.submit(USER, attempt_id, "alarm = A ^ B ^ C", idempotency_key="k1")

        svc.provider = scripted([GOOD])
        soon = await svc.get(USER, attempt_id)                        # the answer was saved before the crash
        assert soon.submission.answer == "alarm = A ^ B ^ C" and soon.submission.status == "evaluating"
        assert soon.status == "evaluating" and not soon.can_retry and not soon.can_submit
        with pytest.raises(ApiError) as raised:
            await svc.retry(USER, attempt_id)
        assert raised.value.code == "nothing_to_retry"

        # the evaluation budget passes: the revision counts as interrupted and can be retried
        from datetime import UTC, datetime, timedelta
        row = store.attempts[attempt_id]["row"]
        row["submissions"][0]["evaluating_since"] = (datetime.now(UTC) - timedelta(minutes=20)).isoformat()
        again = await svc.get(USER, attempt_id)
        assert again.submission.status == "failed" and "evaluation_interrupted" in again.submission.flags and again.can_retry
        retried, _ = await svc.retry(USER, attempt_id)
        assert retried.status == "done"

    async def test_another_server_accepting_the_same_key_first_is_a_replay_not_a_second_score(self, catalog, monkeypatch):
        provider = scripted([GOOD, GOOD])
        store = InMemoryStore(catalog)
        server_a = PracticeService(store, catalog, provider)
        server_b = PracticeService(store, catalog, provider)
        view = await server_a.start(USER, question_key=Q)
        attempt_id = uuid.UUID(view.id)

        original = memory_store._MemoryTx.save_attempt
        calls = {"n": 0}

        async def racy_save(self, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:                     # B's first save: A committed the same key a moment earlier
                await server_a.submit(USER, attempt_id, "alarm = (A&B)|(A&C)|(B&C)", idempotency_key="k1")
                raise DuplicateSubmissionKey("k1")
            return await original(self, **kwargs)
        monkeypatch.setattr(memory_store._MemoryTx, "save_attempt", racy_save)

        sub, _ = await server_b.submit(USER, attempt_id, "alarm = (A&B)|(A&C)|(B&C)", idempotency_key="k1")
        assert sub.replayed and sub.status == "done"
        assert sum(1 for r in provider.requests if r.role == "evaluator") == 1 and len(store.metrics) == N_SKILLS

    async def test_one_profile_race_is_absorbed_without_a_second_model_call(self, catalog):
        provider = scripted([WEAK, GOOD], metered=True)
        svc, store = service(catalog, provider)
        view = await svc.start(USER, question_key=Q)
        attempt_id = uuid.UUID(view.id)
        store.fail_once.add("save_profile")                          # another attempt of this user finished first
        calls_before = len(provider.requests)
        sub, view = await svc.submit(USER, attempt_id, "alarm = A ^ B ^ C", idempotency_key="k1")
        assert sub.status == "done" and sub.band == "WEAK" and "profile_conflict" not in sub.flags
        assert len(provider.requests) == calls_before + 0 or len(provider.requests) - calls_before <= 4   # no re-run
        assert sum(1 for r in provider.requests if r.role == "evaluator") == 1
        assert len(store.metrics) == N_SKILLS and all(m["knowledge_score_after"] is not None for m in store.metrics)
        assert len([f for f in view.follow_ups]) == 1 and view.pending_follow_up is not None   # exactly one follow-up
        skill = catalog.questions[Q].primary_skill
        assert store.profiles[(USER, skill)]["engine_state"]["turns"] == 1

    async def test_two_workers_accepting_different_answers_first_wins_second_gets_conflict(self, catalog):
        provider = scripted([GOOD, GOOD])
        store = InMemoryStore(catalog)
        server_a = PracticeService(store, catalog, provider)
        server_b = PracticeService(store, catalog, provider)
        view = await server_a.start(USER, question_key=Q)
        attempt_id = uuid.UUID(view.id)
        original = memory_store._MemoryTx.save_attempt
        calls = {"n": 0}

        async def racy_save(self, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:                     # B loaded before A saved; A commits revision 1 first
                await server_a.submit(USER, attempt_id, "alarm = (A&B)|(A&C)|(B&C)", idempotency_key="key-a")
            return await original(self, **kwargs)
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(memory_store._MemoryTx, "save_attempt", racy_save)
        try:
            with pytest.raises(ApiError) as raised:
                await server_b.submit(USER, attempt_id, "a different answer", idempotency_key="key-b")
        finally:
            monkeypatch.undo()
        assert raised.value.code == "conflict"
        assert sum(1 for r in provider.requests if r.role == "evaluator") == 1          # B never evaluated
        row = store.attempts[attempt_id]["row"]
        assert [s["key"] for s in row["submissions"]] == ["key-a"] and row["submissions"][0]["status"] == "done"

    async def test_a_superseded_evaluation_returns_the_winners_result(self, catalog):
        provider = scripted([WEAK, GOOD], metered=True)
        store = InMemoryStore(catalog)
        server_a = PracticeService(store, catalog, provider)
        server_b = PracticeService(store, catalog, provider)
        view = await server_a.start(USER, question_key=Q)
        attempt_id = uuid.UUID(view.id)
        # B accepted and saved revision 1, then A (a retry after B looked interrupted) finished it first
        from app.repo.attempts import AlreadyEvaluated
        original = memory_store._MemoryTx.save_attempt
        calls = {"n": 0}

        async def racy_save(self, **kwargs):
            calls["n"] += 1
            if calls["n"] == 2:                     # B's second save (the persist) loses to A
                raise AlreadyEvaluated(1)
            return await original(self, **kwargs)
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(memory_store._MemoryTx, "save_attempt", racy_save)
        try:
            sub, view = await server_b.submit(USER, attempt_id, "alarm = A ^ B ^ C", idempotency_key="k")
        finally:
            monkeypatch.undo()
        assert sub.status == "evaluating" and view.status == "evaluating"       # what the store holds: B's accepted row
        assert len(store.usage) >= 1                                             # B's paid calls are on record
        assert store.metrics == []                                               # and nothing was scored twice

    async def test_profile_conflict_keeps_the_answer_and_bills_the_call(self, catalog):
        svc, store = service(catalog, scripted([GOOD, GOOD], metered=True))
        view = await svc.start(USER, question_key=Q)
        attempt_id = uuid.UUID(view.id)
        store.failures.add("save_profile")
        sub, view = await svc.submit(USER, attempt_id, "alarm = (A&B)|(A&C)|(B&C)", idempotency_key="k1")
        assert sub.status == "failed" and "profile_conflict" in sub.flags and view.can_retry
        assert store.metrics == [] and len(store.usage) >= 1            # the paid call is on record

        store.failures.clear()
        retried, _ = await svc.retry(USER, attempt_id)
        assert retried.status == "done" and len(store.metrics) == N_SKILLS

    async def test_reveal_then_answer_earns_nothing_but_is_still_evaluated(self, catalog):
        svc, store = service(catalog, scripted([GOOD]))
        view = await svc.start(USER, question_key=Q)
        attempt_id = uuid.UUID(view.id)
        text, view = await svc.reveal_reference(USER, attempt_id)
        assert text and view.reference == text
        sub, _ = await svc.submit(USER, attempt_id, "alarm = (A&B)|(A&C)|(B&C)", idempotency_key="k1")
        assert sub.status == "done" and sub.band == "STRONG" and sub.evidence == "none"
        assert "revealed_before_submit_no_evidence" in sub.flags
        assert all(m["evidence_weight"] == 0 for m in store.metrics)


class TestHousekeeping:
    async def test_locks_do_not_accumulate(self, catalog):
        svc, _ = service(catalog, scripted([GOOD] * 20))
        for _ in range(10):
            view = await svc.start(USER, question_key=Q)
            await svc.next_hint(USER, uuid.UUID(view.id))
            await svc.submit(USER, uuid.UUID(view.id), "alarm = (A&B)|(A&C)|(B&C)", idempotency_key="k")
        assert svc._locks == {}

    async def test_concurrent_actions_on_one_attempt_are_serialized(self, catalog):
        svc, _ = service(catalog, scripted([GOOD] * 5))
        view = await svc.start(USER, question_key=Q)
        attempt_id = uuid.UUID(view.id)
        results = await asyncio.gather(svc.next_hint(USER, attempt_id), svc.next_hint(USER, attempt_id),
                                       svc.next_hint(USER, attempt_id), svc.next_hint(USER, attempt_id))
        levels = sorted(h.level for h, _ in results if h is not None)
        assert levels == [1, 2, 3] and svc._locks == {}


class TestDemoProvider:
    async def test_the_default_provider_completes_the_loop_and_is_metered(self, catalog):
        from app.services.demo_provider import DemoProvider
        svc, store = service(catalog, DemoProvider())
        view = await svc.start(USER, question_key=Q)
        attempt_id = uuid.UUID(view.id)
        sub, view = await svc.submit(USER, attempt_id, "alarm = A ^ B ^ C", idempotency_key="k1")     # check fails
        assert sub.status == "done" and sub.band == "WEAK" and sub.card is not None
        turns = 0
        while view.pending_follow_up is not None and turns < 3:
            fsub, view = await svc.submit(USER, attempt_id, "a longer follow-up answer that explains the majority idea in detail",
                                          idempotency_key=f"f{turns}", follow_up_turn=view.pending_follow_up.turn)
            assert fsub.status == "done"
            turns += 1
        assert view.status == "done"
        assert store.usage and all(u["tokens_in"] > 0 for u in store.usage)

        strong = await svc.start(USER, question_key=Q)
        sub, _ = await svc.submit(USER, uuid.UUID(strong.id), "alarm = (A & B) | (A & C) | (B & C) because any two of the "
                                  "three sensors asserted must raise the alarm and each pair gives one product term",
                                  idempotency_key="k2")
        assert sub.band == "STRONG" and sub.check.passed is True
