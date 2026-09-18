"""One simulation turn, end to end, with no I/O.

    evaluation -> check authority -> company emphasis -> band -> scores ->
    skill controller -> subject router -> decision + one metrics row

The caller supplies the Evaluation (from the LLM evaluator) and persists what comes
back. Keeping this pure is what lets persona bots and the replay simulator run
thousands of sessions in a test.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.engine import ENGINE_VERSION, scores, skill_controller, subject_router
from app.engine.params import DEFAULT_PARAMS, EngineParams
from app.schemas.engine import (
    Action,
    Archetype,
    Band,
    CheckResult,
    Decision,
    Evaluation,
    PlanSkill,
    SessionState,
)


@dataclass
class TurnOutcome:
    decision: Decision
    band: Band
    evaluation: Evaluation                 # after check authority and company emphasis
    evidence_weight: float
    metrics: dict = field(default_factory=dict)


class SessionEngine:
    def __init__(self, plan: list[PlanSkill], state: SessionState, *,
                 catalog_min_difficulty: dict[str, int] | None = None,
                 core_misconception_keys: set[str] | None = None,
                 company_emphasis: dict[str, float] | None = None,
                 subject_prior_k: dict[str, float] | None = None,
                 params: EngineParams = DEFAULT_PARAMS):
        self.plan = plan
        self.by_key = {s.key: s for s in plan}
        self.state = state
        self.catalog_min_difficulty = catalog_min_difficulty or {s.key: s.min_difficulty for s in plan}
        self.core_misconception_keys = core_misconception_keys or set()
        self.company_emphasis = company_emphasis
        self.subject_prior_k = subject_prior_k
        self.params = params
        self._last_recovery_pending = False

    # ------------------------------------------------------------------ lifecycle

    def start(self) -> Decision:
        return subject_router.first_decision(self.state, self.plan, subject_prior_k=self.subject_prior_k,
                                             params=self.params)

    def request_hint(self) -> Decision | None:
        """Coach Mode: the user asks for a hint on the current question."""
        skill_state = self.state.skill_state[self.state.current_skill]
        result = skill_controller.request_hint(skill_state, self.params)
        if result is None:
            return None
        return subject_router.route(self.state, self.plan, result, params=self.params)

    def process_turn(self, evaluation: Evaluation, *, archetype: Archetype = Archetype.CONCEPTUAL,
                     check: CheckResult | None = None, latency_ms: int | None = None,
                     revision_count: int | None = None, answer_duration_ms: int | None = None,
                     familiarity: str = "new", exposure_risk: str = "low", turn_elapsed_ms: int = 0,
                     mode: str = "simulation") -> TurnOutcome:
        state, params = self.state, self.params
        plan_skill = self.by_key[state.current_skill]
        skill_state = state.skill_state[plan_skill.key]
        subject = state.subject_state[plan_skill.subject]
        difficulty = state.current_difficulty or plan_skill.min_difficulty
        hint_level = skill_state.hint_level            # the hint that came with the question just answered

        # 1. evaluator output, adjusted by the two authorities above it
        evaluation = scores.apply_check_result(evaluation, check, params)
        evaluation = scores.apply_company_modifiers(evaluation, self.company_emphasis)
        core_misconception = bool(set(evaluation.misconceptions) & self.core_misconception_keys)
        band = scores.classify_band(evaluation, core_misconception, params)

        # 2. scores
        if skill_state.k is None or skill_state.c is None:
            prerequisite_ks = [state.skill_state[p].k for p in plan_skill.prerequisites
                               if p in state.skill_state and state.skill_state[p].k is not None
                               and state.skill_state[p].turns > 0]
            prior = scores.skill_prior(seniority=state.seniority, prerequisite_ks=prerequisite_ks or None,
                                       subject_k=subject.k, params=params)
            skill_state.k = skill_state.k if skill_state.k is not None else prior.k
            skill_state.c = skill_state.c if skill_state.c is not None else prior.c
        weight = scores.evidence_weight(mode, familiarity, hint_level, exposure_risk, params=params)
        update = scores.update_scores(
            k_old=skill_state.k, c_old=skill_state.c, evaluation=evaluation, difficulty=difficulty,
            difficulty_ceiling=state.difficulty_ceiling, turns_on_skill=skill_state.turns,
            hint_level=hint_level, latency_ms=latency_ms, revision_count=revision_count, weight=weight,
            params=params)
        skill_state.k, skill_state.c = update.k_after, update.c_after
        scores.record_turn(skill_state, difficulty=difficulty, band=band, evaluation=evaluation,
                           hint_level=hint_level, weight=weight, core_misconception=core_misconception,
                           archetype=archetype, params=params)
        for observed in state.observed_state.values():
            scores.update_observed(observed, evaluation, archetype, params)

        # 3. subject state, then the two decision layers
        status_before, status_after = subject_router.update_subject_state(state, self.plan, plan_skill.subject,
                                                                         band, params)
        result = skill_controller.decide(
            skill_state, band=band, confidence=skill_state.c, depth=evaluation.depth, plan_skill=plan_skill,
            difficulty_ceiling=state.difficulty_ceiling, catalog_min_difficulty=self.catalog_min_difficulty,
            params=params)

        turn_index = state.turn_index
        state.turn_index += 1
        state.elapsed_ms += turn_elapsed_ms
        state.version += 1
        probe = "; ".join(evaluation.key_points_missed[:2]) or None
        decision = subject_router.route(state, self.plan, result, probe_focus=probe,
                                        subject_prior_k=self.subject_prior_k, params=params)
        if result.resolved:
            # status may have changed when the skill resolved and turns were rebalanced
            status_after = state.subject_state[plan_skill.subject].status

        reason = decision.reason_code if not result.resolved else result.reason_code
        codes = [reason, *decision.rebalance_codes]
        if result.resolved and decision.action == Action.ENTER_SKILL:
            codes.append(decision.reason_code)
        metrics = {
            "mode": mode, "turn_index": turn_index, "band": band.value,
            "subject_key": plan_skill.subject, "subject_status_before": status_before.value,
            "subject_status_after": status_after.value, "subject_turns_used": subject.turns_used,
            "subject_turns_planned": subject.turns_planned,
            "entry_difficulty_reason": decision.entry_difficulty_reason,
            "skill_key": plan_skill.key, "skill_source": plan_skill.source.value,
            "skill_combined_weight": plan_skill.combined_weight,
            "skill_required_level": plan_skill.required_level,
            "question_archetype": archetype.value, "difficulty_asked": difficulty,
            "evidence_weight": weight, "check_passed": check.passed if check else None,
            "familiarity": familiarity,
            "correctness": evaluation.correctness, "depth": evaluation.depth, "clarity": evaluation.clarity,
            "structure": evaluation.structure, "tradeoff_reasoning": evaluation.tradeoff_reasoning,
            "risk_awareness": evaluation.risk_awareness, "hedging_ratio": evaluation.hedging_ratio,
            "observed_skill_scores": {
                key: getattr(evaluation, scores.DIMENSION_FOR_OBSERVED_SKILL[key])
                for key in state.observed_state if key in scores.DIMENSION_FOR_OBSERVED_SKILL},
            "response_latency_ms": latency_ms, "answer_duration_ms": answer_duration_ms,
            "revision_count": revision_count,
            "knowledge_score_before": update.k_before, "knowledge_score_after": update.k_after,
            "confidence_score_before": update.c_before, "confidence_score_after": update.c_after,
            "provisional_level_after": skill_state.provisional_level,
            "decision_action": decision.action.value, "decision_reason_code": ",".join(dict.fromkeys(codes))[:60],
            "difficulty_next": decision.target_difficulty, "skill_next_key": decision.target_skill,
            "subject_next_key": decision.target_subject, "subject_switch": decision.subject_switch,
            "hint_delivered": decision.deliver_hint, "hint_level": decision.hint_level,
            "struggle_budget_remaining": skill_state.budget,
            "recovered_after_hint": result.recovered_after_hint,
            "decision_engine_version": ENGINE_VERSION,
            "eval_flags": [],
        }
        return TurnOutcome(decision=decision, band=band, evaluation=evaluation, evidence_weight=weight,
                           metrics=metrics)
