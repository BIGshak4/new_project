"""AI_Engine_Spec §3.3 transition table, row by row, then the §4.10 session replayed per skill."""

import pytest

from app.engine import skill_controller as sc
from app.schemas.engine import (
    Action,
    AssessmentMode,
    Band,
    Importance,
    PlanSkill,
    SkillSource,
    SkillState,
    SkillStatus,
)

S, P, W = Band.STRONG, Band.PARTIAL, Band.WEAK


def plan_skill(required=4, lo=1, hi=10, prereq=()):
    return PlanSkill(key="skill", subject="subject", source=SkillSource.ROLE, combined_weight=0.1,
                     importance=Importance.CORE, required_level=required,
                     assessment_mode=AssessmentMode.QUESTIONED, planned_turns=3, min_difficulty=lo,
                     max_difficulty=hi, prerequisites=list(prereq))


def state_at(status, difficulty=5, budget=2, **extra):
    return SkillState(key="skill", status=status, current_difficulty=difficulty, budget=budget, **extra)


def decide(state, band, *, confidence=50.0, depth=0.6, skill=None, ceiling=9, mins=None):
    return sc.decide(state, band=band, confidence=confidence, depth=depth, plan_skill=skill or plan_skill(),
                     difficulty_ceiling=ceiling, catalog_min_difficulty=mins)


class TestTransitionTable:
    def test_hold_zone_strong_escalates_one(self):
        state = state_at(SkillStatus.HOLD_ZONE)
        out = decide(state, S)
        assert (out.action, out.reason_code, out.next_difficulty) == (Action.ESCALATE, "strong_answer", 6)
        assert state.status == SkillStatus.ESCALATING

    def test_hold_zone_strong_escalates_two_when_confident_and_deep(self):
        out = decide(state_at(SkillStatus.HOLD_ZONE), S, confidence=80, depth=0.8)
        assert out.next_difficulty == 7
        assert decide(state_at(SkillStatus.HOLD_ZONE), S, confidence=79, depth=0.9).next_difficulty == 6

    def test_escalating_strong_below_ceiling(self):
        out = decide(state_at(SkillStatus.ESCALATING, difficulty=5), S, skill=plan_skill(required=5))
        assert (out.action, out.reason_code, out.next_difficulty) == (Action.ESCALATE, "sustained_strength", 6)

    def test_escalating_strong_at_ceiling_resolves(self):
        state = state_at(SkillStatus.ESCALATING, difficulty=9)
        out = decide(state, S, skill=plan_skill(required=5))
        assert out.resolved and out.reason_code == "ceiling_reached" and state.status == SkillStatus.CEILING_FOUND

    def test_skill_max_difficulty_is_also_a_ceiling(self):
        out = decide(state_at(SkillStatus.ESCALATING, difficulty=7), S, skill=plan_skill(required=5, hi=7))
        assert out.reason_code == "ceiling_reached"

    def test_escalating_strong_one_level_above_requirement_resolves(self):
        # required level 2 -> level 3 is difficulty 5-6
        out = decide(state_at(SkillStatus.ESCALATING, difficulty=6), S, skill=plan_skill(required=2))
        assert out.resolved and out.reason_code == "requirement_exceeded"

    def test_escalating_partial_holds(self):
        state = state_at(SkillStatus.ESCALATING, difficulty=8)
        out = decide(state, P)
        assert (out.action, out.reason_code, out.next_difficulty) == (Action.HOLD, "probe_gap_after_escalation", 8)
        assert state.status == SkillStatus.HOLD_ZONE

    def test_hold_zone_first_partial_probes(self):
        out = decide(state_at(SkillStatus.HOLD_ZONE), P)
        assert (out.action, out.reason_code) == (Action.HOLD, "probe_gap")

    def test_hold_zone_second_partial_confident_resolves(self):
        state = state_at(SkillStatus.HOLD_ZONE, partial_count=1)
        out = decide(state, P, confidence=60)
        assert out.resolved and out.reason_code == "ceiling_found_soft"

    def test_hold_zone_second_partial_unsure_hints(self):
        state = state_at(SkillStatus.HOLD_ZONE, partial_count=1)
        out = decide(state, P, confidence=59)
        assert (out.action, out.reason_code, out.hint_level) == (Action.HINT, "partial_low_confidence", 1)
        assert state.budget == 1 and state.status == SkillStatus.HINTING

    @pytest.mark.parametrize("status", [SkillStatus.HOLD_ZONE, SkillStatus.ESCALATING, SkillStatus.ENTERING])
    def test_weak_with_budget_hints_level_one(self, status):
        out = decide(state_at(status), W)
        assert (out.action, out.reason_code, out.hint_level, out.next_difficulty) == (
            Action.HINT, "weak_answer_budget_available", 1, 5)

    @pytest.mark.parametrize("band", [S, P])
    def test_recovery_after_hint_earns_a_hold_never_an_escalation(self, band):
        state = state_at(SkillStatus.HINTING, hint_level=1, budget=1)
        out = decide(state, band, confidence=95, depth=0.95)
        assert (out.action, out.reason_code, out.next_difficulty) == (Action.HOLD, "recovered_after_hint", 5)
        assert out.recovered_after_hint is True and state.status == SkillStatus.HOLD_ZONE

    def test_hinting_weak_escalates_the_hint(self):
        state = state_at(SkillStatus.HINTING, hint_level=1, budget=1)
        out = decide(state, W)
        assert (out.action, out.reason_code, out.hint_level) == (Action.HINT, "escalate_hint", 2)
        assert state.budget == 0 and out.recovered_after_hint is False

    def test_hint_level_never_passes_three(self):
        state = state_at(SkillStatus.HINTING, hint_level=3, budget=5)
        assert decide(state, W).hint_level == 3

    def test_budget_exhausted_steps_back_two(self):
        state = state_at(SkillStatus.HINTING, hint_level=2, budget=0, difficulty=5)
        out = decide(state, W, skill=plan_skill(lo=1))
        assert (out.action, out.reason_code, out.next_difficulty) == (Action.STEP_BACK, "budget_exhausted", 3)
        assert state.status == SkillStatus.STEPPING_BACK

    def test_step_back_floors_at_the_skill_minimum(self):
        out = decide(state_at(SkillStatus.HINTING, budget=0, difficulty=5), W, skill=plan_skill(lo=4))
        assert out.next_difficulty == 4

    def test_step_back_prefers_a_prerequisite(self):
        skill = plan_skill(prereq=["fifo_verification"])
        out = decide(state_at(SkillStatus.HINTING, budget=0, difficulty=7), W, skill=skill,
                     mins={"fifo_verification": 2})
        assert (out.target_skill, out.next_difficulty) == ("fifo_verification", 3)

    @pytest.mark.parametrize("band", [S, P, W])
    def test_stepping_back_always_resolves(self, band):
        state = state_at(SkillStatus.STEPPING_BACK, difficulty=3, budget=0)
        out = decide(state, band)
        assert out.resolved and out.reason_code == "baseline_mapped" and state.status == SkillStatus.BASELINE_MAPPED


class TestCoachMode:
    def test_requested_hint_starts_at_level_one_and_costs_budget(self):
        state = state_at(SkillStatus.HOLD_ZONE, budget=2)
        out = sc.request_hint(state)
        assert (out.hint_level, out.reason_code, state.budget) == (1, "user_requested_hint", 1)

    def test_no_budget_no_hint(self):
        assert sc.request_hint(state_at(SkillStatus.HOLD_ZONE, budget=0)) is None


def replay(bands_and_conf, *, entry, required, lo=1, hi=10, ceiling=9):
    """Run one skill through the controller. Returns [(difficulty asked, action or reason)]."""
    skill = plan_skill(required=required, lo=lo, hi=hi)
    state = SkillState(key="skill")
    sc.enter_skill(state, entry)
    trail = []
    for band, confidence in bands_and_conf:
        asked = state.current_difficulty
        out = decide(state, band, confidence=confidence, skill=skill, ceiling=ceiling)
        trail.append((asked, out.reason_code if out.resolved else f"{out.action.value}{out.hint_level or ''}"))
        if out.resolved:
            break
    return trail


class TestWorkedSession:
    """AI_Engine_Spec §4.10, senior, ceiling 9. One test per skill's run of turns."""

    def test_turns_1_2_requirement_exceeded(self):
        assert replay([(S, 70), (S, 70)], entry=5, required=2) == [(5, "ESCALATE"), (6, "requirement_exceeded")]

    def test_turns_3_5_soft_ceiling(self):
        assert replay([(S, 70), (P, 70), (P, 70)], entry=7, required=4) == [
            (7, "ESCALATE"), (8, "HOLD"), (8, "ceiling_found_soft")]

    def test_turns_6_9_hint_then_recover_then_resolve(self):
        assert replay([(S, 70), (W, 50), (P, 60), (P, 60)], entry=6, required=4) == [
            (6, "ESCALATE"), (7, "HINT1"), (7, "HOLD"), (7, "ceiling_found_soft")]

    def test_turns_12_16_two_hints_step_back_baseline(self):
        assert replay([(W, 40), (W, 40), (P, 40), (W, 40), (P, 40)], entry=5, required=5, lo=3) == [
            (5, "HINT1"), (5, "HINT2"), (5, "HOLD"), (5, "STEP_BACK"), (3, "baseline_mapped")]

    def test_turns_21_23(self):
        assert replay([(S, 60), (P, 65), (P, 65)], entry=3, required=5) == [
            (3, "ESCALATE"), (4, "HOLD"), (4, "ceiling_found_soft")]
