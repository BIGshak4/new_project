"""Bank-first selection (§1.2), tip rules (§6.4, §6.5) and the Plan Router (§4.11)."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from app.engine import bank, plan_router, tips
from app.engine.catalog import load_catalog
from app.engine.plan import merge_skill_sets
from app.engine.plan_router import ProfileSkill, RecentActivity
from app.schemas.engine import Action, Archetype, Band, EvidenceStatus
from tests.conftest import make_evaluation

SEEDS = Path(__file__).resolve().parent.parent / "seeds"
TODAY = date(2026, 9, 17)


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


@pytest.fixture(scope="module")
def plan(catalog):
    role = catalog.roles["digital-hardware-engineer"]
    return merge_skill_sets(role_rows=role.skill_set, company_rows=[], focus_skill_keys=[], company_weight_share=0,
                            seniority="student", planned_duration_min=45, catalog=catalog.leaf_skills)


# ----------------------------------------------------------------------------- bank


class TestBankSelection:
    def select(self, catalog, **kw):
        defaults = dict(skill="fsm_sequence_detectors", difficulty=5, mode="deep", language="en",
                        allow_in_review=True, require_parity=False)
        return bank.select_question(list(catalog.questions.values()), **{**defaults, **kw})

    def test_picks_the_primary_skill_match(self, catalog):
        assert self.select(catalog).question.key == "example-overlapping-sequence-1011"

    def test_production_rules_serve_nothing_unreviewed(self, catalog):
        assert self.select(catalog, allow_in_review=False, require_parity=True) is None
        assert self.select(catalog, allow_in_review=True, require_parity=True) is None      # parity not checked yet

    def test_difficulty_window(self, catalog):
        assert self.select(catalog, difficulty=9) is None
        assert self.select(catalog, difficulty=6) is not None

    def test_mode_must_be_allowed(self, catalog):
        assert self.select(catalog, mode="quick") is None
        assert self.select(catalog, skill="boolean_algebra", difficulty=2, mode="quick") is not None

    def test_seen_questions_are_not_repeated(self, catalog):
        assert self.select(catalog, seen_keys={"example-overlapping-sequence-1011"}) is None

    def test_unseen_variation_of_a_seen_question(self, catalog):
        base = catalog.questions["example-overlapping-sequence-1011"]
        variation = base.model_copy(update={"key": "fsm_seq_detect_1101_overlap", "variation_of": base.key})
        chosen = bank.select_question([base, variation], skill="fsm_sequence_detectors", difficulty=5, mode="deep",
                                      language="en", seen_keys={base.key}, allow_in_review=True, require_parity=False)
        assert (chosen.question.key, chosen.familiarity) == (variation.key, "seen_variation")

    def test_prefers_the_least_served(self, catalog):
        base = catalog.questions["example-overlapping-sequence-1011"]
        busy = base.model_copy(update={"key": "a_busy", "times_served": 50})
        fresh = base.model_copy(update={"key": "b_fresh", "times_served": 1})
        chosen = bank.select_question([busy, fresh], skill="fsm_sequence_detectors", difficulty=5, mode="deep",
                                      language="en", allow_in_review=True, require_parity=False)
        assert chosen.question.key == "b_fresh"

    def test_archetype_is_a_preference_not_a_wall(self, catalog):
        chosen = self.select(catalog, archetype=Archetype.BEHAVIORAL)
        assert chosen is not None and chosen.relaxed == ["archetype"]

    def test_coverage(self, catalog):
        coverage = bank.coverage_by_skill(list(catalog.questions.values()), language="he", allow_in_review=True,
                                          require_parity=False)
        assert coverage["boolean_algebra"] == {"quick": 1, "deep": 1, "simulation": 1}


# ----------------------------------------------------------------------------- tips


class TestTips:
    def signals(self, **kw):
        evaluation = make_evaluation(**{k: v for k, v in kw.items() if k in (
            "correctness", "depth", "clarity", "structure", "hedging")},
            behavior_signals=kw.get("behavior_signals", []))
        return tips.signals_from(evaluation, band=kw.get("band", Band.PARTIAL), archetype=kw.get("archetype", "design"),
                                 self_confidence=kw.get("self_confidence"), check_passed=kw.get("check_passed"))

    def choose(self, catalog, signals, **kw):
        defaults = dict(turn_index=10, last_delivered_turn={}, timing="mid_session")
        return tips.select_tip(list(catalog.tips.values()), signals, **{**defaults, **kw})

    def test_process_problem_triggers_a_tip(self, catalog):
        choice = self.choose(catalog, self.signals(behavior_signals=["jumped_to_implementation"]))
        assert choice.tip.key == "state_assumptions_first"

    def test_no_tip_while_escalating(self, catalog):
        signals = self.signals(behavior_signals=["jumped_to_implementation"], band=Band.STRONG)
        assert self.choose(catalog, signals) is None
        assert self.choose(catalog, self.signals(behavior_signals=["jumped_to_implementation"]),
                           last_action=Action.ESCALATE) is None

    def test_light_tips_are_held_for_the_report(self, catalog):
        signals = self.signals(structure=0.2, correctness=0.6)
        assert self.choose(catalog, signals) is None                            # severity 3: not mid-session
        assert self.choose(catalog, signals, timing="post_session").tip.key == "structure_your_answer"

    def test_cooldown(self, catalog):
        signals = self.signals(behavior_signals=["jumped_to_implementation"])
        assert self.choose(catalog, signals, turn_index=7, last_delivered_turn={"state_assumptions_first": 4}) is None
        assert self.choose(catalog, signals, turn_index=9, last_delivered_turn={"state_assumptions_first": 4}) is not None

    def test_all_of_must_hold(self, catalog):
        signals = self.signals(behavior_signals=["jumped_to_implementation"], archetype="behavioral")
        assert self.choose(catalog, signals) is None

    def test_calibration_tip(self, catalog):
        signals = self.signals(correctness=0.3, self_confidence=5, band=Band.WEAK)
        assert signals["calibration_gap"] == pytest.approx(0.7)
        chosen = self.choose(catalog, signals, timing="post_session")
        assert chosen.tip.key in ("slow_down_when_sure", "trace_a_second_example")

    def test_render_fills_and_drops_placeholders(self, catalog):
        tip = catalog.tips["state_assumptions_first"].model_copy(
            update={"templates": {"en": "Missed {{missed_point}}. {{unknown}} Next time, try X."}})
        assert tips.render(tip, "en", {"missed_point": "reset"}) == "Missed reset. Next time, try X."

    def test_hebrew_template(self, catalog):
        assert "בפעם הבאה" in tips.render(catalog.tips["cover_every_case"], "he")

    def test_tips_for_gaps(self, catalog):
        ranked = tips.tips_for_gaps(list(catalog.tips.values()), ["fsm_state_tables", "counters"])
        assert ranked[0].key == "cover_every_case"


# ----------------------------------------------------------------------------- plan router


class TestPlanRouter:
    coverage = {"boolean_algebra": {"quick": 1, "deep": 1}, "counters": {"deep": 1},
                "fsm_sequence_detectors": {"deep": 1}, "truth_tables": {"quick": 1}}

    def next(self, plan, profile, **kw):
        defaults = dict(plan=plan, profile=profile, today=TODAY, recent=[], minutes_available_today=30,
                        bank_coverage=self.coverage)
        return plan_router.next_activity(**{**defaults, **kw})

    def test_new_user_starts_with_the_diagnostic(self, plan):
        activity = self.next(plan, {}, diagnostic_done=False)
        assert activity.mode == "diagnostic" and 8 <= len(activity.skills) <= 12

    def test_diagnostic_spreads_across_subjects(self, plan):
        picks = plan_router.diagnostic_skills(plan)
        by_key = {s.key: s.subject for s in plan}
        assert len({by_key[k] for k in picks}) >= 4

    def test_without_evidence_it_explores_the_heaviest_covered_skill(self, plan):
        activity = self.next(plan, {})
        assert activity.reason_code == "unassessed" and activity.skills[0] in self.coverage

    def test_a_core_gap_beats_exploration(self, plan):
        profile = {"counters": ProfileSkill("counters", level=1, status=EvidenceStatus.ASSESSED)}
        activity = self.next(plan, profile)
        assert (activity.skills, activity.reason_code) == (["counters"], "core_gap")

    def test_a_due_retention_check_is_scheduled(self, plan):
        profile = {"counters": ProfileSkill("counters", level=3, status=EvidenceStatus.ASSESSED,
                                            retention_due_at=TODAY - timedelta(days=1))}
        activities = plan_router.candidate_activities(plan=plan, profile=profile, today=TODAY, bank_coverage=self.coverage)
        assert any(a.mode == "retention_check" and a.skills == ["counters"] for a in activities)

    def test_time_penalty(self, plan):
        activity = plan_router.Activity("deep", ["counters"], 20)
        plenty = plan_router.activity_value(activity, plan=plan, profile={}, today=TODAY, recent=[], minutes_available_today=30)
        short = plan_router.activity_value(activity, plan=plan, profile={}, today=TODAY, recent=[], minutes_available_today=5)
        assert plenty - short == pytest.approx(1.5)

    def test_variety_bonus_and_fatigue_penalty(self, plan):
        profile = {"counters": ProfileSkill("counters", level=1, status=EvidenceStatus.ASSESSED)}
        hard = plan_router.Activity("deep", ["counters"], 20, hard=True)
        base = plan_router.activity_value(hard, plan=plan, profile=profile, today=TODAY, recent=[], minutes_available_today=30)
        tired = plan_router.activity_value(hard, plan=plan, profile=profile, today=TODAY, minutes_available_today=30,
                                           recent=[RecentActivity("quick", "WEAK"), RecentActivity("quick", "WEAK")])
        assert tired == pytest.approx(base + 0.3 - 0.8)

    def test_final_days_are_reserved_for_simulation_and_retention(self, plan):
        profile = {s.key: ProfileSkill(s.key, level=3, status=EvidenceStatus.ASSESSED) for s in plan}
        assert self.next(plan, profile, days_to_interview=3, week_index=2).mode == "simulation"

    def test_weekly_plan_respects_minutes_and_has_a_deep_practice(self, plan):
        items = plan_router.weekly_plan(plan=plan, profile={}, week_start=TODAY, minutes_per_day=25,
                                        bank_coverage=self.coverage)
        assert items and any(i.activity.mode == "deep" for i in items)
        for day in range(7):
            assert sum(i.activity.estimated_minutes for i in items if i.day_index == day) <= 25 + 20
        assert len({(i.activity.mode, tuple(i.activity.skills)) for i in items}) == len(items)

    def test_week_two_adds_a_simulation_when_time_allows(self, plan):
        items = plan_router.weekly_plan(plan=plan, profile={}, week_start=TODAY, minutes_per_day=45,
                                        bank_coverage=self.coverage, week_index=1)
        assert any(i.activity.mode == "simulation" for i in items)

    def test_retention_scheduling(self):
        assert plan_router.schedule_retention(level_before=2, level_after=3, today=TODAY) == TODAY + timedelta(days=4)
        assert plan_router.schedule_retention(level_before=3, level_after=3, today=TODAY) is None
        assert plan_router.schedule_retention(level_before=None, level_after=2, today=TODAY) is None   # first assessment
        due, passed = plan_router.after_retention_check(passed=True, today=TODAY, checks_passed=0)
        assert (due, passed) == (TODAY + timedelta(days=12), 1)
        assert plan_router.after_retention_check(passed=False, today=TODAY, checks_passed=2) == (None, 0)

    def test_reason_cites_history_and_stays_general_without_it(self, catalog, plan):
        labels = catalog.skill_labels()
        gap = plan_router.Activity("deep", ["counters"], 20, reason_code="core_gap",
                                   reason_facts={"skill": "counters", "level": 1, "required": 2})
        assert plan_router.reason_text(gap, "en", labels) == \
            "Counters is a core skill for your target role, and you are at level 1 of the 2 it needs."
        thin = plan_router.Activity("deep", ["counters"], 20, reason_code="core_gap",
                                    reason_facts={"skill": "counters", "level": None, "required": 2})
        assert "no evidence" in plan_router.reason_text(thin, "en", labels)
        assert "Counters" in plan_router.reason_text(gap, "he", labels)
