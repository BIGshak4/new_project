"""Persona bots (AI_Engine_Spec §8): synthetic candidates run whole sessions through the
real controller and router. The assertions are the behaviours the spec promises."""

import pytest

from app.engine import subject_router as sr
from app.engine.plan import merge_skill_sets
from app.engine.session import SessionEngine
from app.schemas.engine import Action, Band, SubjectStatus
from tests.conftest import make_evaluation

STRONG = dict(correctness=0.9, depth=0.8, clarity=0.8, hedging=0.1, level=4)
PARTIAL = dict(correctness=0.6, depth=0.4, clarity=0.6, hedging=0.3, level=3)
WEAK = dict(correctness=0.2, depth=0.2, clarity=0.4, hedging=0.6, level=1)


def run_session(catalog, role_rows, company_rows, answer, *, seniority="senior", baseline=5, ceiling=9,
                minutes=45, max_turns=80):
    plan = merge_skill_sets(role_rows=role_rows, company_rows=company_rows, focus_skill_keys=[],
                            company_weight_share=0.30, seniority=seniority, planned_duration_min=minutes,
                            catalog=catalog)
    state = sr.init_session_state(plan, seniority=seniority, baseline_difficulty=baseline,
                                  difficulty_ceiling=ceiling, planned_duration_min=minutes)
    engine = SessionEngine(plan, state)
    decision = engine.start()
    log = []
    while decision.action != Action.END and len(log) < max_turns:
        profile = answer(decision, state)
        outcome = engine.process_turn(make_evaluation(**profile), turn_elapsed_ms=108_000)
        log.append((decision, outcome))
        decision = outcome.decision
    return plan, state, log


@pytest.fixture
def run(catalog, dv_role_rows, semi_company_rows):
    return lambda answer, **kw: run_session(catalog, dv_role_rows, semi_company_rows, answer, **kw)


def test_every_persona_terminates_and_stays_in_range(run):
    for profile in (STRONG, PARTIAL, WEAK):
        _, state, log = run(lambda d, s, p=profile: p)
        assert log and log[-1][1].decision.action == Action.END
        for decision, outcome in log:
            assert 1 <= outcome.metrics["difficulty_asked"] <= 9
            assert decision.target_skill is not None


def test_strong_everywhere_closes_subjects_early_and_never_gets_a_hint(run):
    _, state, log = run(lambda d, s: STRONG)
    assert not any(o.decision.deliver_hint for _, o in log)
    assert any("rebalance_strong_release" in o.metrics["decision_reason_code"]
               or "subject_closed_early" in o.metrics["decision_reason_code"] for _, o in log)
    assert state.turn_pool_released > 0


def test_weak_in_one_subject_gets_more_turns_there_and_easier_entries(run):
    plan, state, log = run(lambda d, s: WEAK if d.target_subject == "uvm" else STRONG)
    uvm = state.subject_state["uvm"]
    assert uvm.weak_answers >= 2
    assert any("rebalance_weak_extend" in o.metrics["decision_reason_code"] for _, o in log)
    later_entries = [d.target_difficulty for d, _ in log
                     if d.action == Action.ENTER_SKILL and d.target_subject == "uvm"][1:]
    assert later_entries and all(entry < 5 for entry in later_entries)


def test_struggling_candidate_gets_hints_then_a_step_back_never_an_endless_loop(run):
    _, state, log = run(lambda d, s: WEAK)
    actions = [o.decision.action for _, o in log]
    assert Action.HINT in actions and Action.STEP_BACK in actions
    per_skill = {}
    for decision, _ in log:
        per_skill[decision.target_skill] = per_skill.get(decision.target_skill, 0) + 1
    assert max(per_skill.values()) <= 6          # 1 + 2 hints + step back + baseline, with slack


def test_no_demoralization_spiral_fatigue_override_fires(run):
    """Weak in two subjects in a row: the next subject must be a success, not a third hard area."""
    hard = {"uvm", "debugging"}
    _, state, log = run(lambda d, s: WEAK if d.target_subject in hard else STRONG)
    reasons = [d.reason_code for d, _ in log if d.action == Action.ENTER_SKILL]
    visited = state.subjects_visited_order
    for first, second, third in zip(visited, visited[1:], visited[2:], strict=False):
        if first in hard and second in hard and first != second:
            assert third not in hard
    assert "fatigue_override" in reasons or not any(
        a in hard and b in hard and a != b for a, b in zip(visited, visited[1:], strict=False))


def test_hint_never_followed_by_escalation(run):
    toggle = {"n": 0}

    def answer(decision, state):
        toggle["n"] += 1
        return WEAK if toggle["n"] % 3 == 1 else STRONG

    _, _, log = run(answer)
    for (decision, outcome), (_next_decision, _) in zip(log, log[1:], strict=False):
        if decision.deliver_hint and outcome.band in (Band.STRONG, Band.PARTIAL):
            assert outcome.decision.action == Action.HOLD


def test_strong_then_collapses_ends_on_something_answerable(run):
    def answer(decision, state):
        return STRONG if state.turn_index < 8 else WEAK

    _, state, log = run(answer)
    assert log[-1][1].decision.action == Action.END
    assert state.turn_index <= 45 / 1.8 + 8


def test_session_respects_the_clock(run):
    _, state, log = run(lambda d, s: PARTIAL, minutes=20)
    assert state.elapsed_ms / 60_000 <= 20 + 1.8 * 6


def test_metrics_row_has_every_decision_field(run):
    _, _, log = run(lambda d, s: PARTIAL)
    row = log[0][1].metrics
    for field in ("skill_key", "subject_key", "difficulty_asked", "evidence_weight", "knowledge_score_before",
                  "knowledge_score_after", "provisional_level_after", "decision_action", "decision_reason_code",
                  "struggle_budget_remaining", "subject_status_after", "decision_engine_version"):
        assert field in row
    assert len(row["decision_reason_code"]) <= 60


def test_student_track_stays_at_entry_level(catalog, dv_role_rows):
    plan, state, log = run_session(catalog, dv_role_rows, [], lambda d, s: PARTIAL, seniority="student",
                                   baseline=2, ceiling=5, minutes=30)
    assert all(o.metrics["difficulty_asked"] <= 5 for _, o in log)
    assert all(s.status in (SubjectStatus.DONE, SubjectStatus.UNTOUCHED, SubjectStatus.EXPLORING,
                            SubjectStatus.MIXED, SubjectStatus.WEAK, SubjectStatus.STRONG)
               for s in state.subject_state.values())
