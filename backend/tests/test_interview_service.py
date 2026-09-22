"""Mock interviews over the in-memory store: bank-only questions, hidden results, one score per turn, a report at the end."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.api.errors import ApiError
from app.engine.catalog import load_catalog
from app.engine.providers import LLMError, LLMRequest, ScriptedProvider
from app.services import memory_store
from app.services.interview_service import DURATIONS, MAX_TURNS, InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from tests.test_practice_hardening import GOOD, SEEDS, WEAK

USER = uuid.uuid4()
OTHER = uuid.uuid4()
REPORT = "## Summary\nA steady interview with one weak subject."


def interviewer(replies, *, fail_first_evaluation: bool = False):
    """Evaluator replies cycle through `replies`; the report role gets a fixed narrative."""
    queue, calls = list(replies), {"n": 0}

    def respond(request: LLMRequest):
        if request.role == "evaluator":
            calls["n"] += 1
            if fail_first_evaluation and calls["n"] == 1:
                raise LLMError("model down", retryable=False)
            return queue[(calls["n"] - 1) % len(queue)]
        if request.role == "report":
            return REPORT
        return "unused"
    return ScriptedProvider(respond)


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


class Clock:
    """The interview clock in tests: every answer takes `step` minutes."""

    def __init__(self, step_min: float = 2.5):
        self.now = datetime(2026, 9, 22, 9, 0, tzinfo=UTC)
        self.step = timedelta(minutes=step_min)

    def __call__(self):
        return self.now

    def advance(self):
        self.now += self.step


def service(catalog, provider, **config) -> tuple[InterviewService, InMemoryStore]:
    store = InMemoryStore(catalog)
    svc = InterviewService(store, catalog, provider, InterviewConfig(reviewed_only=False, **config))
    svc.clock = Clock()
    return svc, store


async def run_to_the_end(svc, user, view, answer="a careful, correct answer", limit=MAX_TURNS + 2):
    sid = uuid.UUID(view.id)
    asked = []
    while view.status == "in_progress" and view.current_turn is not None and len(asked) < limit:
        asked.append(view.current_turn.question_key)
        svc.clock.advance()
        _, view = await svc.answer(user, sid, view.current_turn.index, answer, idempotency_key=f"t{view.current_turn.index}")
    return view, asked


class TestAWholeInterview:
    async def test_start_answer_finish_report(self, catalog):
        svc, store = service(catalog, interviewer([GOOD, GOOD, WEAK]))
        svc.clock = Clock(step_min=2)
        view = await svc.start(USER, duration_min=45, language="en")
        assert view.status == "in_progress" and view.current_turn is not None and view.turn_count == 1
        assert view.current_turn.status == "open" and view.current_turn.band is None and view.can_answer
        assert view.plan and all(p.planned_turns >= 0 for p in view.plan)
        assert view.remaining_min == 45 and view.results_revealed is False and view.report_ready is False
        first_key = view.current_turn.question_key
        assert first_key in catalog.questions                      # from the bank, never generated

        view, asked = await run_to_the_end(svc, USER, view)
        assert view.status == "completed" and view.report_ready and view.results_revealed
        assert view.current_turn is None and len(view.turns) == len(asked) >= 2
        assert all(t.band in ("STRONG", "PARTIAL", "WEAK") and t.summary is not None for t in view.turns)
        assert len(set(asked)) == len(asked), "the same question was asked twice"
        assert all(k in catalog.questions for k in asked)

        report = await svc.report(USER, uuid.UUID(view.id))
        assert report.narrative_md == REPORT and report.narrative_source == "generated"
        assert "session_overall" in report.fit and "role" in report.fit
        assert report.fit["session_overall"].skills_total >= len(view.plan)      # plan skills plus observed ones
        assert report.skills and all(s.label for s in report.skills)
        assert any(s.status == "assessed" and s.proficiency_level is not None for s in report.skills)
        assert all(s.proficiency_level is None for s in report.skills if s.status == "not_assessed")
        assert len(report.turns) == len(asked) and report.timeline
        # the profile continued through the interview and metrics were written per turn
        assert store.profiles and len([m for m in store.metrics if m.get("session_id")]) == len(asked)
        assert all(u["mode"] == "simulation" for u in store.usage)
        again = await svc.report(USER, uuid.UUID(view.id))                # narrative generated once, then cached
        assert again.narrative_md == REPORT

    async def test_results_stay_hidden_until_the_end_and_a_refresh_restores_the_state(self, catalog):
        svc, store = service(catalog, interviewer([WEAK, GOOD]))
        view = await svc.start(USER, duration_min=30)
        sid = uuid.UUID(view.id)
        turn, view = await svc.answer(USER, sid, 0, "alarm = A ^ B ^ C", idempotency_key="k0")
        assert turn.status == "done" and turn.band is None and turn.summary is None       # hidden mid-interview
        assert view.turns[0].band is None and view.current_turn.index == 1
        restored = await svc.get(USER, sid)
        assert restored.model_dump() == view.model_dump()
        # a second service instance (another server) sees the same session
        other = InterviewService(store, catalog, interviewer([GOOD]), InterviewConfig(reviewed_only=False))
        assert (await other.get(USER, sid)).current_turn.index == 1

    async def test_replay_conflict_and_ownership(self, catalog):
        svc, _ = service(catalog, interviewer([GOOD]))
        view = await svc.start(USER, duration_min=20)
        sid = uuid.UUID(view.id)
        turn, view = await svc.answer(USER, sid, 0, "answer", idempotency_key="same")
        replay, _ = await svc.answer(USER, sid, 0, "answer", idempotency_key="same")
        assert replay.index == 0 and replay.status == "done"
        with pytest.raises(ApiError, match="already answered"):
            await svc.answer(USER, sid, 0, "another answer", idempotency_key="different")
        with pytest.raises(ApiError, match="not found"):
            await svc.get(OTHER, sid)
        with pytest.raises(ApiError):
            await svc.answer(USER, sid, 5, "x", idempotency_key="k")
        with pytest.raises(ApiError, match="answer is required"):
            await svc.answer(USER, sid, view.current_turn.index, "   ", idempotency_key="k9")

    async def test_hints_come_from_the_bank_and_cost_budget(self, catalog):
        svc, _ = service(catalog, interviewer([GOOD]))
        view = await svc.start(USER, duration_min=20)
        sid = uuid.UUID(view.id)
        if not view.can_hint:
            pytest.skip("the first question has no bank hint")
        hint, view = await svc.hint(USER, sid)
        assert hint is not None and hint.level == 1 and hint.text and view.hints_used == 1
        assert view.current_turn.hints[0].text == hint.text
        second, view = await svc.hint(USER, sid)
        assert second is None or second.level == 2

    async def test_end_early_gives_a_report_from_what_was_answered(self, catalog):
        svc, _ = service(catalog, interviewer([GOOD]))
        view = await svc.start(USER, duration_min=45)
        sid = uuid.UUID(view.id)
        _, view = await svc.answer(USER, sid, 0, "answer", idempotency_key="k0")
        view = await svc.end(USER, sid)
        assert view.status == "completed" and view.ended_early and view.current_turn is None
        report = await svc.report(USER, sid)
        assert report.turn_count >= 1 and report.fit["session_overall"].skills_assessed <= 1
        with pytest.raises(ApiError, match="over"):
            await svc.answer(USER, sid, 1, "late", idempotency_key="late")

    async def test_a_failed_evaluation_keeps_the_answer_and_allows_another_try(self, catalog):
        svc, _ = service(catalog, interviewer([GOOD], fail_first_evaluation=True))
        view = await svc.start(USER, duration_min=20)
        sid = uuid.UUID(view.id)
        turn, view = await svc.answer(USER, sid, 0, "first try", idempotency_key="k0")
        assert turn.status == "failed" and turn.answer == "first try" and view.can_answer and view.status == "in_progress"
        turn, view = await svc.answer(USER, sid, 0, "second try", idempotency_key="k1")
        assert turn.status == "done" and view.current_turn.index == 1

    async def test_daily_limit_and_duration_validation(self, catalog):
        svc, _ = service(catalog, interviewer([GOOD]), daily_limit=1)
        await svc.start(USER, duration_min=20)
        with pytest.raises(ApiError, match="limit"):
            await svc.start(USER, duration_min=20)
        with pytest.raises(ApiError, match="duration"):
            await svc.start(OTHER, duration_min=25)
        assert DURATIONS == (20, 30, 45)


class TestResilience:
    async def test_a_stale_evaluation_is_treated_as_failed_and_can_be_answered_again(self, catalog):
        svc, store = service(catalog, interviewer([GOOD]))
        view = await svc.start(USER, duration_min=20)
        sid = uuid.UUID(view.id)
        # the process died right after "answer saved, evaluating": the row says evaluating since 10 minutes ago
        turn = store.sessions[sid]["turns"][0]
        turn["question_generation_meta"].update(status="evaluating", idempotency_key="lost-tab",
                                                evaluating_since=(svc.clock() - timedelta(minutes=10)).isoformat())
        turn["answer_text"] = "an answer that was never scored"
        stuck = await svc.get(USER, sid)
        assert stuck.status == "in_progress" and stuck.can_answer and stuck.current_turn.status == "failed"
        result, view = await svc.answer(USER, sid, 0, "the answer again", idempotency_key="new-tab")
        assert result.status == "done" and view.current_turn.index == 1

    async def test_a_crash_inside_the_evaluation_leaves_a_failed_turn_not_a_stuck_one(self, catalog):
        def respond(request):
            if request.role == "evaluator":
                raise RuntimeError("boom")
            return "unused"
        svc, store = service(catalog, ScriptedProvider(respond))
        view = await svc.start(USER, duration_min=20)
        sid = uuid.UUID(view.id)
        with pytest.raises(RuntimeError):
            await svc.answer(USER, sid, 0, "answer", idempotency_key="k0")
        view = await svc.get(USER, sid)
        assert view.can_answer and view.current_turn.status == "failed" and view.current_turn.answer == "answer"
        assert "evaluation_crashed" in store.sessions[sid]["turns"][0]["question_generation_meta"]["flags"]

    async def test_two_writers_cannot_both_score_the_same_turn(self, catalog, monkeypatch):
        svc, store = service(catalog, interviewer([GOOD]))
        view = await svc.start(USER, duration_min=20)
        sid = uuid.UUID(view.id)
        original = memory_store._MemoryTx.load_session

        async def load_then_race(self, session_id, *, user_id):
            stored = await original(self, session_id, user_id=user_id)
            self.s.sessions[session_id]["row"]["state"]["revision"] += 1      # another server writes right after our read
            return stored
        monkeypatch.setattr(memory_store._MemoryTx, "load_session", load_then_race)
        with pytest.raises(ApiError, match="another request"):
            await svc.answer(USER, sid, 0, "answer", idempotency_key="k0")
        assert not [m for m in store.metrics if m.get("session_id") == sid]        # nothing was scored

    async def test_a_new_interview_reports_only_its_own_evidence(self, catalog):
        svc, store = service(catalog, interviewer([GOOD]))
        first = await svc.start(USER, duration_min=20)
        first, asked = await run_to_the_end(svc, USER, first)
        assert store.profiles                                              # the profile carried the evidence forward
        turns_before = {k: v["engine_state"]["turns"] for k, v in store.profiles.items()}
        second = await svc.start(USER, duration_min=20)
        second = await svc.end(USER, uuid.UUID(second.id))
        report = await svc.report(USER, uuid.UUID(second.id))
        assert report.fit["session_overall"].skills_assessed == 0 and report.fit["session_overall"].fit_score is None
        assert all(s.turns_count == 0 for s in report.skills)
        assert {k: v["engine_state"]["turns"] for k, v in store.profiles.items()} == turns_before

    async def test_profile_history_continues_across_practice_and_interviews(self, catalog):
        svc, store = service(catalog, interviewer([GOOD]))
        view = await svc.start(USER, duration_min=20)
        sid = uuid.UUID(view.id)
        skill = view.current_turn.skill
        svc.clock.advance()
        await svc.answer(USER, sid, 0, "answer", idempotency_key="k0")
        state = store.profiles[(USER, skill)]["engine_state"]
        assert state["turns"] == 1 and len(state["history"]) == 1 and state["k"] is not None

    async def test_a_narrative_failure_is_not_cached(self, catalog):
        failures = {"n": 1}

        def respond(request):
            if request.role == "evaluator":
                return GOOD
            if request.role == "report":
                if failures["n"]:
                    failures["n"] -= 1
                    raise LLMError("report model down", retryable=False)
                return REPORT
            return "unused"
        svc, _ = service(catalog, ScriptedProvider(respond))
        view = await svc.start(USER, duration_min=20)
        sid = uuid.UUID(view.id)
        await svc.answer(USER, sid, 0, "answer", idempotency_key="k0")
        await svc.end(USER, sid)
        first = await svc.report(USER, sid)
        assert first.narrative_source == "fallback" and first.narrative_md
        second = await svc.report(USER, sid)
        assert second.narrative_source == "generated" and second.narrative_md == REPORT

    async def test_the_clock_runs_while_a_question_is_open(self, catalog):
        svc, _ = service(catalog, interviewer([GOOD]))
        view = await svc.start(USER, duration_min=20)
        assert view.remaining_min == 20
        svc.clock.now += timedelta(minutes=5)
        assert (await svc.get(USER, uuid.UUID(view.id))).remaining_min == 15


class TestReviewedOnly:
    async def test_nothing_reviewed_means_no_interview(self, catalog):
        store = InMemoryStore(catalog)
        svc = InterviewService(store, catalog, interviewer([GOOD]), InterviewConfig())   # reviewed_only=True
        with pytest.raises(ApiError) as excinfo:
            await svc.start(USER, duration_min=20)
        assert excinfo.value.code == "no_reviewed_questions" and excinfo.value.status == 409
        assert not store.sessions

    async def test_only_covered_skills_are_planned(self, catalog):
        svc, _ = service(catalog, interviewer([GOOD]))
        view = await svc.start(USER, duration_min=45, language="he")
        covered = {q.primary_skill for q in catalog.questions.values()}
        assert view.plan and all(p.skill in covered for p in view.plan)
        assert view.language == "he" and any("֐" <= ch <= "ת" for ch in view.current_turn.question)
