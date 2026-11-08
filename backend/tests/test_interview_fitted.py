"""Shaked, 2026-11-02: "i want the interview to be fitted to the person, i dont want the user to feel bad, i want him
to try more". Four mechanics on the in-memory store:

* a weak answer brings the engine's hint WITH the next question (the HINT decision used to be made and never shown);
* an interview that would end on a weak answer asks one closing question on a strength, then ends whatever the band;
* the report opens with what held up and proposes the next interview; a second interview says what changed;
* finishing earns coins once, whatever the result, once enough questions were answered.
The judge is untouched: nothing here changes how an answer is graded.
"""

from __future__ import annotations

import uuid

import pytest

from app.engine import generator
from app.engine.catalog import load_catalog
from app.schemas.engine import RESOLVED_STATUSES, Action, Decision, SkillStatus
from app.services.coins import CoinsService, load_rules
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from tests.test_interview_service import Clock, interviewer, run_to_the_end
from tests.test_practice_hardening import GOOD, SEEDS, WEAK

RULES = load_rules(SEEDS / "coins.json")


@pytest.fixture(scope="module")
def catalog():
    """The seed bank as production serves it: ASSESS_UNREVIEWED_QUESTIONS is on there (§5zx), so every generated
    question is assessable and most skills have several questions to choose from. This module's own instance."""
    loaded = load_catalog(SEEDS)
    for question in loaded.questions.values():
        if question.assets.get("assessment_ready") is False:
            question.assets["assessment_ready"] = True
    return loaded


def service(catalog, provider, *, step_min: float = 2.5, coins: bool = False, **config):
    store = InMemoryStore(catalog)
    wallet = CoinsService(store, RULES) if coins else None
    svc = InterviewService(store, catalog, provider, InterviewConfig(reviewed_only=False, **config), coins=wallet)
    svc.clock = Clock(step_min=step_min)
    return svc, store


def engine_state(store, session_id):
    return store.sessions[session_id]["row"]["state"]["engine"]


class TestTheHintArrivesWithTheNextQuestion:
    async def test_a_weak_answer_brings_a_nudge(self, catalog):
        svc, store = service(catalog, interviewer([WEAK, GOOD]))
        user = uuid.uuid4()
        view = await svc.start(user, duration_min=45, language="en")
        sid = uuid.UUID(view.id)
        assert view.current_turn.hints == [] and view.hints_used == 0        # the opening question comes bare
        _, view = await svc.answer(user, sid, 0, "I am not sure, maybe an OR gate", idempotency_key="k0")
        assert view.status == "in_progress" and view.current_turn is not None
        first = store.sessions[sid]["turns"][0]["question_generation_meta"]
        assert first["band"] == "WEAK" and first["action_after"] == "HINT", "the controller hints after a weak answer"
        nxt = view.current_turn
        question = catalog.questions[nxt.question_key]
        assert nxt.skill == view.turns[0].skill, "the nudge comes on the same skill"
        assert nxt.hints and nxt.hints[0].level >= 1 and nxt.hints[0].text == generator.bank_hint(question, nxt.hints[0].level, "en")
        assert view.hints_used == 1                                          # counted as a hint the interview gave
        assert store.sessions[sid]["row"].get("hints_requested_by_user", 0) == 0   # ...not one the candidate asked for
        meta = store.sessions[sid]["turns"][1]["question_generation_meta"]
        assert meta["hint_level"] == nxt.hints[0].level and meta["hint_delivered"] is True

    async def test_the_judge_and_the_rewards_see_the_delivered_hint(self, catalog):
        """The delivered hint discounts XP exactly like a requested one: the view says so once results are revealed."""
        svc, store = service(catalog, interviewer([WEAK, GOOD]), step_min=12)   # 2 answers end a 20-minute interview
        user = uuid.uuid4()
        view = await svc.start(user, duration_min=20, language="en")
        sid = uuid.UUID(view.id)
        _, view = await svc.answer(user, sid, 0, "not sure", idempotency_key="k0")
        assert view.current_turn is not None and view.current_turn.hints, "the nudge came with the next question"
        delivered = view.current_turn.hints[0].level
        view, _ = await run_to_the_end(svc, user, view)
        assert view.status == "completed"
        second = next(t for t in view.turns if t.index == 1)
        assert second.band == "STRONG" and second.hints[0].level == delivered
        assert second.xp_earned is None                                         # XP is gone (Shaked, 2026-11-06)
        meta = store.sessions[sid]["turns"][1]["question_generation_meta"]
        assert meta["hint_level"] == delivered                                  # the judge and the coin rule saw the nudge

    def test_the_richest_hint_the_question_has_up_to_the_engines_level(self, catalog):
        svc, _ = service(catalog, interviewer([GOOD]))
        question = next(q for q in catalog.questions.values() if len(q.text("en").hints) >= 3)
        row = {"hints_used": 0}

        def delivered(level: int, q) -> dict:
            turn = {"question_generation_meta": {"hint_level": 0, "hints": []}}
            svc._deliver_hint(turn, q, Decision(action=Action.HINT, reason_code="x", deliver_hint=True, hint_level=level),
                              "en", row)
            return turn["question_generation_meta"]

        assert delivered(2, question)["hint_level"] == 2 and delivered(2, question)["hints"][0]["text"] == question.text("en").hints[1]
        one_hint = question.model_copy(deep=True)
        one_hint.text("en").hints = [one_hint.text("en").hints[0]]
        assert delivered(3, one_hint)["hint_level"] == 1                       # the engine wanted 3; the question has 1
        none = question.model_copy(deep=True)
        none.text("en").hints = []
        assert "hint_delivered" not in delivered(1, none) and delivered(1, none)["hints"] == []
        held = {"question_generation_meta": {"hint_level": 0, "hints": []}}
        svc._deliver_hint(held, question, Decision(action=Action.HOLD, reason_code="x"), "en", row)
        assert held["question_generation_meta"]["hints"] == []                 # only a HINT decision delivers
        assert row["hints_used"] == 3


class TestEndOnAWin:
    async def test_a_weak_last_answer_gets_one_closing_question_on_a_strength(self, catalog):
        # three answers of seven minutes end a twenty-minute interview; the third is weak
        svc, store = service(catalog, interviewer([GOOD, GOOD, WEAK]), step_min=7)
        user = uuid.uuid4()
        view = await svc.start(user, duration_min=20, language="en")
        sid = uuid.UUID(view.id)
        for index in range(3):
            svc.clock.advance()
            _, view = await svc.answer(user, sid, view.current_turn.index, f"answer {index}", idempotency_key=f"k{index}")
        turns = store.sessions[sid]["turns"]
        assert turns[2]["question_generation_meta"]["band"] == "WEAK"
        assert view.status == "in_progress" and view.current_turn is not None, "one more question, not the end"
        closing = view.current_turn
        assert closing.closing is True and closing.index == 3
        snapshot = turns[3]["question_generation_meta"]["closing"]
        strong_keys = {t["skill_key"] for t in turns[:2]}
        assert closing.skill in strong_keys and snapshot["skill"] == closing.skill
        strong_difficulty = max(t["difficulty"] for t in turns[:2] if t["skill_key"] == closing.skill)
        assert turns[3]["difficulty"] == strong_difficulty
        assert "difficulty" not in closing.model_dump()
        assert len({t["question_key"] for t in turns}) == 4                  # never the same question twice

        # the closing answer is judged like any other, the interview ends whatever the band, and the skill keeps
        # the status it had resolved with
        svc.clock.advance()
        last, view = await svc.answer(user, sid, 3, "a weak closing answer", idempotency_key="k3")
        assert view.status == "completed" and view.current_turn is None and not view.ended_early
        assert last.band in ("STRONG", "PARTIAL", "WEAK") and last.closing is True
        turns = store.sessions[sid]["turns"]                                 # the store hands out copies: re-read
        assert turns[3]["question_generation_meta"]["action_after"] == "END"
        state = engine_state(store, sid)
        assert SkillStatus(state["skill_state"][closing.skill]["status"]) == SkillStatus(snapshot["status"])
        assert len(state["skill_state"][closing.skill]["history"]) >= 2      # the evidence stayed
        report = await svc.report(user, sid, narrative=False)
        assert report.turns[-1].closing is True and report.turn_count == 4
        assert all("difficulty" not in entry for entry in report.timeline)
        assert len([m for m in store.metrics if m.get("session_id")]) == 4  # the closing turn has its metrics row

    async def test_a_strong_last_answer_ends_without_a_closing_question(self, catalog):
        svc, store = service(catalog, interviewer([GOOD]), step_min=25)
        user = uuid.uuid4()
        view = await svc.start(user, duration_min=20, language="en")
        sid = uuid.UUID(view.id)
        svc.clock.advance()
        _, view = await svc.answer(user, sid, 0, "a strong answer", idempotency_key="k0")
        assert view.status == "completed" and len(view.turns) == 1 and not view.turns[0].closing

    async def test_a_weak_first_and_only_answer_closes_on_the_easiest_question_of_the_skill(self, catalog):
        svc, store = service(catalog, interviewer([WEAK]), step_min=25)
        user = uuid.uuid4()
        view = await svc.start(user, duration_min=20, language="en")
        sid = uuid.UUID(view.id)
        svc.clock.advance()
        _, view = await svc.answer(user, sid, 0, "not sure", idempotency_key="k0")
        if view.status == "completed":
            pytest.skip("the bank has no second question for the opening skill")
        closing = view.current_turn
        plan_skill = next(p for p in view.plan if p.skill == closing.skill)
        assert closing.closing and closing.skill == view.turns[0].skill
        turns = store.sessions[sid]["turns"]
        assert turns[closing.index]["difficulty"] <= turns[0]["difficulty"] and plan_skill is not None
        svc.clock.advance()
        _, view = await svc.answer(user, sid, closing.index, "still not sure", idempotency_key="k1")
        assert view.status == "completed"

    async def test_ending_early_never_adds_a_closing_question(self, catalog):
        svc, _ = service(catalog, interviewer([WEAK]))
        user = uuid.uuid4()
        view = await svc.start(user, duration_min=20, language="en")
        sid = uuid.UUID(view.id)
        _, view = await svc.answer(user, sid, 0, "not sure", idempotency_key="k0")
        view = await svc.end(user, sid)
        assert view.status == "completed" and view.ended_early and not any(t.closing for t in view.turns)


class TestTheReportInvitesTheNextInterview:
    async def test_what_held_up_comes_first_and_a_next_step_is_proposed(self, catalog):
        svc, _ = service(catalog, interviewer([GOOD, GOOD, WEAK]), step_min=4)
        user = uuid.uuid4()
        view = await svc.start(user, duration_min=20, language="en")
        view, _ = await run_to_the_end(svc, user, view)
        report = await svc.report(user, uuid.UUID(view.id), narrative=False)
        strong_skills = {t.skill for t in report.turns if t.band == "STRONG"}
        assert report.held_up and {s.key for s in report.held_up} & strong_skills
        assert report.next_step is not None and report.next_step.step in ("harder", "same", "easier")
        assert report.next_step.duration_min == 20
        assert report.since_last_time == [] and report.previous_session_id is None and report.fit_change is None
        text = report.narrative_md
        assert text.startswith("## Summary") and "What held up" in text and "Next time" in text
        assert text.index("What held up") < text.index("## Subjects"), "strengths before the subject table"
        assert "%" not in text.split("\n## Subjects")[0].replace("Fit:", "") or "Fit:" in text   # the fit line is the only number up top

    async def test_hebrew_fallback_uses_hebrew_headings(self, catalog):
        svc, _ = service(catalog, interviewer([GOOD]), step_min=25)
        user = uuid.uuid4()
        view = await svc.start(user, duration_min=20, language="he")
        view, _ = await run_to_the_end(svc, user, view)
        report = await svc.report(user, uuid.UUID(view.id), narrative=False)
        assert "## סיכום" in report.narrative_md and "בפעם הבאה" in report.narrative_md

    async def test_the_second_interview_says_what_changed(self, catalog):
        svc, _ = service(catalog, interviewer([WEAK, WEAK, GOOD, GOOD]), step_min=12)
        user = uuid.uuid4()
        first = await svc.start(user, duration_min=20, language="en")
        first, _ = await run_to_the_end(svc, user, first)                    # two weak answers (plus a closing one)
        first_report = await svc.report(user, uuid.UUID(first.id), narrative=False)
        assert first_report.previous_session_id is None
        svc.clock.advance()
        second = await svc.start(user, duration_min=20, language="en")
        second, _ = await run_to_the_end(svc, user, second)                  # strong answers now
        report = await svc.report(user, uuid.UUID(second.id), narrative=False)
        assert report.previous_session_id == first.id
        assert report.since_last_time, "skills assessed in both interviews are compared"
        assert all(c.change in ("improved", "held", "lower", "new") for c in report.since_last_time)
        assert all(c.after is not None for c in report.since_last_time)
        assert report.fit_change in ("higher", "same", "lower", None)
        assert "Since last time" in report.narrative_md
        # the first interview's report does not change because a second one happened later
        again = await svc.report(user, uuid.UUID(first.id), narrative=False)
        assert again.previous_session_id is None and again.since_last_time == []

    async def test_the_narrative_payload_carries_the_new_facts(self, catalog):
        seen = {}

        def respond(request):
            if request.role == "report":
                seen["user"] = request.user
                seen["version"] = request.prompt_version
                return "## What held up\nfine"
            return GOOD
        from app.engine.providers import ScriptedProvider
        svc, store = service(catalog, ScriptedProvider(respond), step_min=25)
        user = uuid.uuid4()
        view = await svc.start(user, duration_min=20, language="en")
        view, _ = await run_to_the_end(svc, user, view)
        sid = uuid.UUID(view.id)
        store.sessions[sid]["row"]["state"]["narrative"] = "Question difficulty 2"
        plain = await svc.report(user, sid, narrative=False)
        assert plain.narrative_source == "fallback" and "Question difficulty" not in plain.narrative_md
        report = await svc.report(user, sid)
        assert report.narrative_source == "generated" and seen["version"] == "report.v3"
        assert "difficulty" not in seen["user"] and "demonstrated_ceiling" not in seen["user"]
        assert '"held_up"' in seen["user"] and '"next_step"' in seen["user"] and '"since_last_time"' in seen["user"]


class TestFinishingEarnsCoins:
    """Shaked, 2026-11-07: "rewarded by the ability to finish it and the ability to have strong answers; coins will
    become real money". The finishing bonus is the interview's own strong-turn earnings, paid once, only when it ran
    to its end: an all-weak interview earns nothing, and so does ending early."""

    def finish_rows(self, store, user):
        return [(r["kind"], r["delta"]) for r in store.coin_ledger if r["user_id"] == user and r["reference"].endswith(":finished")]

    async def test_an_all_weak_interview_finishes_with_nothing(self, catalog):
        svc, store = service(catalog, interviewer([WEAK, WEAK, WEAK, WEAK]), step_min=4, coins=True)
        user = uuid.uuid4()
        view = await svc.start(user, duration_min=20, language="en")
        view, asked = await run_to_the_end(svc, user, view)
        assert view.status == "completed" and len(asked) >= RULES.interview_finished_min_turns
        assert self.finish_rows(store, user) == []
        report = await svc.report(user, uuid.UUID(view.id), narrative=False)
        assert report.completion_coins == 0 and all(t.coins_earned == 0 for t in report.turns if t.band == "WEAK")

    async def test_finishing_doubles_what_the_strong_turns_earned_once(self, catalog):
        svc, store = service(catalog, interviewer([GOOD, GOOD, GOOD, GOOD]), step_min=5, coins=True)
        user = uuid.uuid4()
        view = await svc.start(user, duration_min=20, language="en")
        view, asked = await run_to_the_end(svc, user, view)
        assert view.status == "completed" and not view.ended_early and len(asked) >= 3
        report = await svc.report(user, uuid.UUID(view.id), narrative=False)
        turn_coins = sum(t.coins_earned or 0 for t in report.turns)
        assert turn_coins == RULES.strong_interview_turn * len(asked)      # four first-time questions, ten each
        assert report.completion_coins == turn_coins == int(turn_coins * RULES.interview_finish_bonus_share)
        assert self.finish_rows(store, user) == [("earn", turn_coins)]
        await svc.report(user, uuid.UUID(view.id))                          # the narrative save re-persists the row
        assert self.finish_rows(store, user) == [("earn", turn_coins)]      # paid once
        balance = (await svc.coins.wallet(user)).balance
        assert balance == RULES.starting_gift + 2 * turn_coins

    async def test_ending_early_keeps_the_turn_coins_but_forfeits_the_bonus(self, catalog):
        svc, store = service(catalog, interviewer([GOOD, GOOD, GOOD]), step_min=2, coins=True)
        user = uuid.uuid4()
        view = await svc.start(user, duration_min=45, language="en")
        sid = uuid.UUID(view.id)
        for index in range(3):
            svc.clock.advance()
            _, view = await svc.answer(user, sid, view.current_turn.index, f"strong {index}", idempotency_key=f"k{index}")
        view = await svc.end(user, sid)
        assert view.status == "completed" and view.ended_early
        report = await svc.report(user, sid, narrative=False)
        assert sum(t.coins_earned or 0 for t in report.turns) == 3 * RULES.strong_interview_turn
        assert report.completion_coins == 0 and self.finish_rows(store, user) == []

    async def test_start_and_quit_earns_nothing(self, catalog):
        svc, store = service(catalog, interviewer([GOOD]), coins=True)
        user = uuid.uuid4()
        view = await svc.start(user, duration_min=20, language="en")
        _, view = await svc.answer(user, uuid.UUID(view.id), 0, "one answer", idempotency_key="k0")
        view = await svc.end(user, uuid.UUID(view.id))
        assert view.status == "completed" and self.finish_rows(store, user) == []
        report = await svc.report(user, uuid.UUID(view.id), narrative=False)
        assert report.completion_coins == 0

    def test_the_seed_carries_the_numbers_and_the_rule(self):
        from app.services.coins import coins_for_finish
        assert (RULES.interview_finish_bonus_share, RULES.interview_finished_min_turns) == (1.0, 3)
        assert coins_for_finish(RULES, answered_turns=3, earned_in_interview=30) == 30
        assert coins_for_finish(RULES, answered_turns=2, earned_in_interview=20) == 0          # too few answers
        assert coins_for_finish(RULES, answered_turns=5, earned_in_interview=0) == 0           # nothing strong
        assert coins_for_finish(RULES, answered_turns=5, earned_in_interview=50, ended_early=True) == 0


def test_resolved_statuses_cover_the_closing_restore():
    """The snapshot restores a SkillStatus by value; every resolved status must round-trip."""
    assert all(SkillStatus(s.value) is s for s in RESOLVED_STATUSES)
