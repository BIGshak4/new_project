"""AI_Engine_Spec §4: subject state, next subject, next skill, entry difficulty, rebalancing, bridges."""

import pytest

from app.engine import subject_router as sr
from app.engine.plan import merge_skill_sets
from app.engine.skill_controller import ControllerResult
from app.schemas.engine import (
    Action,
    Band,
    Bridge,
    SkillStatus,
    SubjectStatus,
)

S, P, W = Band.STRONG, Band.PARTIAL, Band.WEAK


@pytest.fixture
def plan(catalog, dv_role_rows, semi_company_rows):
    return merge_skill_sets(role_rows=dv_role_rows, company_rows=semi_company_rows, focus_skill_keys=[],
                            company_weight_share=0.30, seniority="senior", planned_duration_min=45,
                            catalog=catalog)


@pytest.fixture
def state(plan):
    return sr.init_session_state(plan, seniority="senior", baseline_difficulty=5, difficulty_ceiling=9,
                                 planned_duration_min=45)


def resolve(state, key, level, *, k=70.0, turns=2):
    skill = state.skill_state[key]
    skill.status, skill.provisional_level, skill.k, skill.c, skill.turns = SkillStatus.CEILING_FOUND, level, k, 65.0, turns


def touch(state, plan, subject, bands):
    for band in bands:
        sr.update_subject_state(state, plan, subject, band)


class TestInit:
    def test_observed_skills_are_not_question_targets(self, state):
        assert "risk_awareness" in state.observed_state and "risk_awareness" not in state.skill_state

    def test_subject_with_only_observed_skills_is_never_visited(self, state):
        assert state.subject_state["engineering_judgment"].status == SubjectStatus.DONE

    def test_subject_inherits_weight_importance_turns(self, state, plan):
        uvm = state.subject_state["uvm"]
        members = [s for s in plan if s.subject == "uvm"]
        assert uvm.weight == pytest.approx(sum(s.combined_weight for s in members), abs=1e-3)
        assert uvm.importance.value == "core"
        assert uvm.turns_planned == sum(s.planned_turns for s in members)


class TestSubjectStatus:
    def test_untouched_then_exploring(self, state, plan):
        assert state.subject_state["uvm"].status == SubjectStatus.UNTOUCHED
        state.skill_state["uvm_sequences"].turns = 1
        touch(state, plan, "uvm", [P])
        assert state.subject_state["uvm"].status == SubjectStatus.EXPLORING

    def test_strong_needs_two_resolved_level_margin_and_no_weak_answer(self, state, plan):
        resolve(state, "sv_assertions", 5)
        resolve(state, "sv_randomization", 5)
        state.subject_state["systemverilog"].skills_planned = 3        # pretend one skill is still open
        touch(state, plan, "systemverilog", [S])
        assert state.subject_state["systemverilog"].status == SubjectStatus.STRONG
        touch(state, plan, "systemverilog", [W])
        assert state.subject_state["systemverilog"].status != SubjectStatus.STRONG

    def test_mixed_one_above_one_below(self, state, plan):
        resolve(state, "uvm_sequences", 4)               # required 4: meets
        resolve(state, "uvm_scoreboard_monitor", 2)      # required 4: below
        touch(state, plan, "uvm", [P])
        assert state.subject_state["uvm"].status == SubjectStatus.MIXED

    def test_weak_by_two_weak_answers(self, state, plan):
        state.skill_state["debugging_methodology"].turns = 2
        state.skill_state["debugging_methodology"].provisional_level = 4
        state.subject_state["debugging"].skills_planned = 2
        touch(state, plan, "debugging", [W, W])
        assert state.subject_state["debugging"].status == SubjectStatus.WEAK

    def test_weak_by_level_one_below_requirement(self, state, plan):
        skill = state.skill_state["debugging_methodology"]
        skill.turns, skill.provisional_level, skill.k = 2, 3, 40.0       # required 5
        state.subject_state["debugging"].skills_planned = 2
        touch(state, plan, "debugging", [P, P])
        assert state.subject_state["debugging"].status == SubjectStatus.WEAK

    def test_done_when_all_resolved(self, state, plan):
        resolve(state, "debugging_methodology", 3)
        touch(state, plan, "debugging", [P])
        assert state.subject_state["debugging"].status == SubjectStatus.DONE


class TestEntryDifficulty:
    """The four worked examples in §4.5: senior, baseline 5, ceiling 9."""

    def skill(self, plan, key):
        return next(s for s in plan if s.key == key)

    def test_momentum_plus_one_into_untouched_subject(self, state, plan):
        state.recent_bands = [S, S, S]
        entry, reason = sr.entry_difficulty(state, plan, self.skill(plan, "uvm_sequences"))
        assert entry == 6 and reason == {"baseline": 5, "subject_adjust": 0, "prerequisite_adjust": 0, "momentum_adjust": 1}

    def test_strong_subject_plus_two(self, state, plan):
        state.subject_state["uvm"].status = SubjectStatus.STRONG
        assert sr.entry_difficulty(state, plan, self.skill(plan, "fsm_coverage"))[0] == 7

    def test_prerequisite_below_requirement_minus_one(self, state, plan):
        resolve(state, "fifo_verification", 2)           # required 3
        entry, reason = sr.entry_difficulty(state, plan, self.skill(plan, "ooo_scoreboard"))
        assert reason["prerequisite_adjust"] == -1
        assert entry == 5        # 5 - 1 = 4, then clamped up to the skill's min_difficulty of 5

    def test_prerequisite_below_requirement_without_clamp(self, state, plan):
        resolve(state, "fifo_verification", 2)
        skill = self.skill(plan, "ooo_scoreboard").model_copy(update={"min_difficulty": 1})
        assert sr.entry_difficulty(state, plan, skill)[0] == 4

    def test_weak_subject_minus_two(self, state, plan):
        state.subject_state["debugging"].status = SubjectStatus.WEAK
        assert sr.entry_difficulty(state, plan, self.skill(plan, "debugging_methodology"))[0] == 3

    def test_prerequisite_met_plus_one_and_high_k_plus_one(self, state, plan):
        resolve(state, "fifo_verification", 4)
        state.subject_state["hw_queues"].k = 75.0
        state.subject_state["hw_queues"].status = SubjectStatus.EXPLORING
        assert sr.entry_difficulty(state, plan, self.skill(plan, "ooo_scoreboard"))[0] == 7     # turn 18

    def test_mixed_and_low_k_minus_one(self, state, plan):
        state.subject_state["uvm"].status, state.subject_state["uvm"].k = SubjectStatus.MIXED, 50.0
        assert sr.entry_difficulty(state, plan, self.skill(plan, "uvm_scoreboard_monitor"))[0] == 4

    def test_never_more_than_three_above_or_two_below(self, state, plan):
        state.subject_state["uvm"].status = SubjectStatus.STRONG
        state.recent_bands = [S, S, S, S]
        skill = self.skill(plan, "uvm_sequences").model_copy(update={"prerequisites": []})
        assert sr.entry_difficulty(state, plan, skill)[0] <= 8
        state.subject_state["uvm"].status = SubjectStatus.WEAK
        state.recent_bands = [W, W, W, W]
        assert sr.entry_difficulty(state, plan, skill)[0] == 3

    def test_session_ceiling_wins(self, state, plan):
        state.difficulty_ceiling = 6
        state.subject_state["uvm"].status = SubjectStatus.STRONG
        assert sr.entry_difficulty(state, plan, self.skill(plan, "uvm_sequences"))[0] == 6


class TestChooseSubject:
    def test_first_subject_is_core(self, state, plan):
        decision = sr.first_decision(state, plan)
        assert decision.action == Action.ENTER_SKILL
        assert state.subject_state[decision.target_subject].importance.value == "core"
        assert decision.target_difficulty == 5 and decision.subject_switch

    def test_stays_in_a_subject_until_covered(self, state, plan):
        sr.first_decision(state, plan)
        current = state.current_subject
        others = [s for s in plan if s.subject == current and s.key != state.current_skill and s.key in state.skill_state]
        if not others:
            pytest.skip("first subject has a single skill")
        resolve(state, state.current_skill, 4)
        touch(state, plan, current, [S])
        assert sr.choose_subject(state, plan).subject == current

    def test_fatigue_override_picks_a_strong_subject(self, state, plan):
        for key in ("debugging", "hw_queues"):
            state.subject_state[key].final_momentum = -1.0
            state.subject_state[key].turns_used = 3
        state.subjects_visited_order = ["debugging", "hw_queues"]
        state.current_subject = "hw_queues"
        state.subject_state["systemverilog"].status = SubjectStatus.STRONG
        choice = sr.choose_subject(state, plan)
        assert (choice.subject, choice.reason_code) == ("systemverilog", "fatigue_override")

    def test_fatigue_override_falls_back_to_best_known_untouched(self, state, plan):
        for key in ("debugging", "hw_queues"):
            state.subject_state[key].final_momentum = -1.0
        state.subjects_visited_order = ["debugging", "hw_queues"]
        choice = sr.choose_subject(state, plan, subject_prior_k={"values": 90.0, "uvm": 40.0})
        assert (choice.subject, choice.reason_code) == ("values", "fatigue_override")

    def test_one_bad_subject_is_not_fatigue(self, state):
        state.subject_state["debugging"].final_momentum = -1.0
        state.subject_state["uvm"].final_momentum = 0.5
        state.subjects_visited_order = ["uvm", "debugging"]
        assert not sr.fatigue_active(state)

    def test_ending_override_takes_the_top_unresolved_core_skill(self, state, plan):
        state.elapsed_ms = 40 * 60_000          # 5 minutes left
        choice = sr.choose_subject(state, plan)
        assert choice.reason_code == "ending_override"
        assert next(s for s in plan if s.key == choice.skill).importance.value == "core"

    def test_strong_subject_yields_time(self, state, plan):
        subject = state.subject_state["systemverilog"]
        base = sr.subject_score(state, plan, subject, fatigue=False)
        subject.status = SubjectStatus.STRONG
        assert sr.subject_score(state, plan, subject, fatigue=False) < base

    def test_no_ping_pong(self, state, plan):
        subject = state.subject_state["uvm"]
        base = sr.subject_score(state, plan, subject, fatigue=False)
        subject.left_at_turn, state.turn_index, state.current_subject = 4, 5, "debugging"
        assert sr.subject_score(state, plan, subject, fatigue=False) == pytest.approx(base - 0.5)


class TestChooseSkill:
    def test_prerequisite_comes_first(self, state, plan):
        assert sr.choose_skill(state, plan, "hw_queues").key == "fifo_verification"      # turn 17

    def test_dependent_after_prerequisite_resolves(self, state, plan):
        resolve(state, "fifo_verification", 4)
        assert sr.choose_skill(state, plan, "hw_queues").key == "ooo_scoreboard"

    def test_core_beats_heavier_non_core(self, state, plan):
        assert sr.choose_skill(state, plan, "uvm").importance.value == "core"


class TestRebalance:
    def test_strong_subject_releases_turns_to_open_core_skills(self, state, plan):
        resolve(state, "sv_assertions", 4, turns=3)      # meets the requirement; 5 would close the subject early
        state.subject_state["systemverilog"].status = SubjectStatus.STRONG
        before = dict(state.skill_turns_planned)
        codes = sr.rebalance(state, plan, "systemverilog")
        assert "rebalance_strong_release" in codes
        assert state.skill_turns_planned["sv_randomization"] < before["sv_randomization"]
        assert state.turn_pool_released > 0
        gained = [k for k in before if state.skill_turns_planned[k] > before[k]]
        assert gained and all(next(s for s in plan if s.key == k).subject != "systemverilog" for k in gained)

    def test_strong_release_applies_once(self, state, plan):
        state.subject_state["systemverilog"].status = SubjectStatus.STRONG
        sr.rebalance(state, plan, "systemverilog")
        assert sr.rebalance(state, plan, "systemverilog") == []

    def test_weak_subject_extends_within_cap(self, state, plan):
        subject = state.subject_state["uvm"]
        subject.status = SubjectStatus.WEAK
        original = subject.turns_planned_original
        codes = sr.rebalance(state, plan, "uvm")
        assert "rebalance_weak_extend" in codes
        assert original < subject.turns_planned <= round(original * 1.5 + 0.5)

    def test_core_skills_exceeded_closes_the_subject_early(self, state, plan):
        resolve(state, "uvm_sequences", 5)               # required 4 -> 5 is required + 1
        resolve(state, "uvm_scoreboard_monitor", 5)
        codes = sr.rebalance(state, plan, "uvm")         # fsm_coverage (important) is still open
        assert "subject_closed_early" in codes
        assert state.subject_state["uvm"].status == SubjectStatus.DONE


class TestRoute:
    def test_unresolved_keeps_the_skill_and_carries_the_probe(self, state, plan):
        sr.first_decision(state, plan)
        skill = state.current_skill
        decision = sr.route(state, plan, ControllerResult(Action.HOLD, "probe_gap", False, next_difficulty=5),
                            probe_focus="tag reuse")
        assert (decision.target_skill, decision.probe_focus, decision.subject_switch) == (skill, "tag reuse", False)

    def test_hint_decision(self, state, plan):
        sr.first_decision(state, plan)
        decision = sr.route(state, plan, ControllerResult(Action.HINT, "weak_answer_budget_available", False,
                                                          next_difficulty=5, hint_level=1))
        assert decision.deliver_hint and decision.hint_level == 1

    def test_resolved_with_under_four_minutes_ends(self, state, plan):
        sr.first_decision(state, plan)
        state.elapsed_ms = 42 * 60_000
        decision = sr.route(state, plan, ControllerResult(None, "ceiling_found_soft", True))
        assert (decision.action, decision.reason_code) == (Action.END, "time_up")

    def test_plan_complete_ends(self, state, plan):
        sr.first_decision(state, plan)
        for subject in state.subject_state.values():
            subject.status, subject.closed_early = SubjectStatus.DONE, True
        assert sr.route(state, plan, ControllerResult(None, "baseline_mapped", True)).reason_code == "plan_complete"

    def test_observed_core_skill_short_on_evidence_is_invited_after_halfway(self, state, plan):
        sr.first_decision(state, plan)
        state.elapsed_ms = 23 * 60_000
        decision = sr.route(state, plan, ControllerResult(Action.HOLD, "probe_gap", False, next_difficulty=5))
        assert decision.invite_observed_skills == ["risk_awareness"]
        assert decision.target_archetype.value in ("design", "debugging")


class TestBridges:
    def test_returning_to_a_weak_subject_is_a_fresh_start(self, state):
        target = state.subject_state["debugging"]
        target.status = SubjectStatus.WEAK
        assert sr.choose_bridge(state, target, fatigue_override=False, last_subject=False) == Bridge.FRESH_START

    def test_fatigue_override_never_mentions_the_struggle(self, state):
        target = state.subject_state["systemverilog"]
        assert sr.choose_bridge(state, target, fatigue_override=True, last_subject=False) == Bridge.CLEAN_TOPIC

    def test_strength_reference(self, state):
        state.current_subject = "systemverilog"
        state.subject_state["systemverilog"].status = SubjectStatus.STRONG
        assert sr.choose_bridge(state, state.subject_state["uvm"], fatigue_override=False,
                                last_subject=False) == Bridge.STRENGTH_REFERENCE

    def test_last_area(self, state):
        assert sr.choose_bridge(state, state.subject_state["values"], fatigue_override=False,
                                last_subject=True) == Bridge.LAST_AREA
