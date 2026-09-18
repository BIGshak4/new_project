"""Randomized sessions: whatever the candidate does, the engine keeps its promises."""

import random

import pytest

from app.engine import subject_router as sr
from app.engine.plan import merge_skill_sets
from app.engine.session import SessionEngine
from app.schemas.engine import Action, AssessmentMode, SubjectStatus
from tests.conftest import make_evaluation

PROFILES = [
    dict(correctness=0.9, depth=0.8, clarity=0.8, hedging=0.1, level=4),
    dict(correctness=0.6, depth=0.4, clarity=0.6, hedging=0.3, level=3),
    dict(correctness=0.2, depth=0.2, clarity=0.4, hedging=0.6, level=1),
]


def run_random_session(catalog, role_rows, company_rows, seed: int):
    rng = random.Random(seed)
    seniority = rng.choice(["student", "junior", "mid", "senior"])
    baseline = {"student": 2, "junior": 2, "mid": 4, "senior": 5}[seniority]
    ceiling = {"student": 5, "junior": 6, "mid": 8, "senior": 9}[seniority]
    minutes = rng.choice([10, 20, 30, 45, 60])
    share = rng.choice([0.0, 0.3])
    plan = merge_skill_sets(role_rows=role_rows, company_rows=company_rows if share else [], focus_skill_keys=[],
                            company_weight_share=share, seniority=seniority, planned_duration_min=minutes,
                            catalog=catalog)
    state = sr.init_session_state(plan, seniority=seniority, baseline_difficulty=baseline,
                                  difficulty_ceiling=ceiling, planned_duration_min=minutes)
    engine = SessionEngine(plan, state)
    by_key = {s.key: s for s in plan}
    decision = engine.start()
    turns = 0
    resolved_seen: set[str] = set()
    while decision.action != Action.END:
        turns += 1
        assert turns <= 120, f"seed {seed}: session did not terminate"
        skill = by_key[decision.target_skill]
        assert skill.assessment_mode == AssessmentMode.QUESTIONED, f"seed {seed}: targeted an observed skill"
        low, high = skill.min_difficulty, min(skill.max_difficulty, ceiling)
        if low <= high:
            assert low <= decision.target_difficulty <= high, f"seed {seed}: difficulty {decision.target_difficulty} outside [{low}, {high}] for {skill.key}"
        if decision.action == Action.ENTER_SKILL:
            assert decision.target_skill not in resolved_seen, f"seed {seed}: re-entered resolved skill {decision.target_skill}"
        assert 0 <= decision.hint_level <= 3
        outcome = engine.process_turn(make_evaluation(**rng.choice(PROFILES)), turn_elapsed_ms=rng.choice([60_000, 108_000, 150_000]))
        for skill_state in state.skill_state.values():
            assert skill_state.budget >= 0, f"seed {seed}: negative budget on {skill_state.key}"
            if skill_state.resolved:
                resolved_seen.add(skill_state.key)
        decision = outcome.decision
    for subject in state.subject_state.values():
        assert subject.turns_used == sum(state.skill_state[s.key].turns for s in plan
                                         if s.subject == subject.key and s.key in state.skill_state), f"seed {seed}: subject turn count drifted"
    return state, turns


@pytest.mark.parametrize("seed", list(range(40)))
def test_random_sessions_keep_the_invariants(catalog, dv_role_rows, semi_company_rows, seed):
    state, turns = run_random_session(catalog, dv_role_rows, semi_company_rows, seed)
    assert turns >= 1
    assert state.elapsed_ms / 60_000 <= state.planned_duration_min + 2.5      # at most one turn past the clock


def test_subject_status_is_refreshed_when_its_last_skill_resolves(catalog, dv_role_rows):
    """Resolving a skill must be visible to the router in the same turn (rebalancing, subject choice)."""
    plan = merge_skill_sets(role_rows=dv_role_rows, company_rows=[], focus_skill_keys=[], company_weight_share=0,
                            seniority="senior", planned_duration_min=45, catalog=catalog)
    state = sr.init_session_state(plan, seniority="senior", baseline_difficulty=5, difficulty_ceiling=9,
                                  planned_duration_min=45)
    engine = SessionEngine(plan, state)
    decision = engine.start()
    strong = dict(correctness=0.9, depth=0.8, clarity=0.8, hedging=0.1, level=4)
    while decision.action != Action.END:
        outcome = engine.process_turn(make_evaluation(**strong), turn_elapsed_ms=60_000)
        row = outcome.metrics
        subject = state.subject_state[row["subject_key"]]
        if subject.status == SubjectStatus.DONE and outcome.decision.subject_switch:
            assert row["subject_status_after"] == "done"
            break
        decision = outcome.decision


def test_skill_min_difficulty_above_session_ceiling_is_clamped_not_crashed(catalog, dv_role_rows):
    plan = merge_skill_sets(role_rows=dv_role_rows, company_rows=[], focus_skill_keys=[], company_weight_share=0,
                            seniority="student", planned_duration_min=20, catalog=catalog)
    state = sr.init_session_state(plan, seniority="student", baseline_difficulty=2, difficulty_ceiling=4,
                                  planned_duration_min=20)                     # ooo_scoreboard has min_difficulty 5
    engine = SessionEngine(plan, state)
    decision = engine.start()
    while decision.action != Action.END:
        assert 1 <= decision.target_difficulty <= 5
        decision = engine.process_turn(make_evaluation(correctness=0.6, depth=0.4), turn_elapsed_ms=90_000).decision
