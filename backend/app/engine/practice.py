"""Deep and quick practice: one question, end to end (AI_Engine_Spec §1.1, §6.6).

    hints (bank, levels 1-3) -> submit -> deterministic check -> evaluator -> band ->
    evidence weight -> scores per examined skill -> feedback card + at most one tip ->
    skill controller -> optional follow-up (probe, scaffold, step back, one escalation)

Everything the caller must persist comes back in the outcome: the attempt fields,
one metrics row per examined skill, and one usage event per model call.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.engine import ENGINE_VERSION, checks, evaluator, feedback, generator, scores, skill_controller, tips
from app.engine.evaluator import EvaluationResult
from app.engine.feedback import FeedbackCard
from app.engine.params import DEFAULT_PARAMS, EngineParams
from app.engine.providers import LLMUsage, Provider
from app.schemas.bank import BankQuestion, Tip
from app.schemas.engine import (
    Action,
    AssessmentMode,
    Band,
    CatalogSkill,
    CheckResult,
    Decision,
    Evaluation,
    Importance,
    PlanSkill,
    SkillSource,
    SkillState,
)

MAX_FOLLOW_UPS = 2


@dataclass
class PracticeContext:
    provider: Provider
    skills: dict[str, CatalogSkill]
    language: str = "en"
    seniority: str = "student"
    difficulty_ceiling: int = 5
    required_levels: dict[str, int] = field(default_factory=dict)
    skill_weights: dict[str, float] = field(default_factory=dict)
    tips: list[Tip] = field(default_factory=list)
    glossary: list[dict] = field(default_factory=list)
    role_family: str | None = "hardware"
    polish_tips: bool = True
    params: EngineParams = DEFAULT_PARAMS


@dataclass
class UsageEvent:
    action: str
    model: str
    usage: LLMUsage
    latency_ms: int

    def as_row(self, mode: str) -> dict:
        return {"mode": mode, "action": self.action, "model": self.model, "tokens_in": self.usage.input_tokens,
                "tokens_out": self.usage.output_tokens, "cache_read_tokens": self.usage.cache_read_tokens,
                "cache_write_tokens": self.usage.cache_write_tokens, "cost_usd": self.usage.cost_usd(self.model),
                "latency_ms": self.latency_ms}


@dataclass
class PracticeOutcome:
    band: Band | None
    evaluation: Evaluation | None
    check: CheckResult | None
    evidence_weight: float
    card: FeedbackCard | None
    tip_text: str | None
    tip_key: str | None
    follow_up: str | None                      # the next question to show, or None when the attempt is complete
    decision: Decision | None
    metrics: list[dict] = field(default_factory=list)
    usage: list[UsageEvent] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


class PracticeAttempt:
    def __init__(self, ctx: PracticeContext, question: BankQuestion, skill_states: dict[str, SkillState], *,
                 mode: str = "deep", evidence_mode: str | None = None, familiarity: str = "new",
                 self_confidence: int | None = None):
        self.ctx, self.question = ctx, question
        self.skill_states = skill_states
        self.mode = mode                                   # attempt.mode: quick | deep
        self.evidence_mode = evidence_mode or mode         # also diagnostic | retention_check (AI_Engine_Spec §2.9)
        self.familiarity = familiarity
        self.self_confidence = self_confidence
        self.hints_used = 0
        self.reference_revealed = False
        self.revealed_before_submit = False
        self.submitted = False
        self.follow_up_turns: list[dict] = []
        self.misconceptions_hit: list[str] = []
        self.band: Band | None = None
        self.evaluation: Evaluation | None = None
        self.check: CheckResult | None = None
        self._pending_follow_up: generator.GeneratedQuestion | None = None
        self._follow_up_difficulty = question.difficulty
        self._escalated = False
        self._tip_turns: dict[str, int] = {}

        primary = question.primary_skill
        catalog_skill = ctx.skills[primary]
        self.plan_skill = PlanSkill(
            key=primary, subject=catalog_skill.subject or question.subject, source=SkillSource.ROLE,
            combined_weight=ctx.skill_weights.get(primary, 0.1), importance=Importance.IMPORTANT,
            required_level=ctx.required_levels.get(primary, 2), assessment_mode=AssessmentMode.QUESTIONED,
            min_difficulty=catalog_skill.min_difficulty, max_difficulty=catalog_skill.max_difficulty,
            prerequisites=list(catalog_skill.prerequisites))
        state = self._state(primary)
        skill_controller.enter_skill(state, question.difficulty, ctx.params)
        # the profile's state is long-lived; every attempt starts with a fresh struggle budget
        state.budget = ctx.params.controller.struggle_budget_per_skill

    # ------------------------------------------------------------------ before submitting

    def prompt(self) -> str:
        return generator.from_bank(self.question, self.ctx.language).question.question_text

    def next_hint(self) -> tuple[int, str] | None:
        """Bank hints, one level at a time (AI_Engine_Spec §6.3). Each one lowers the evidence weight."""
        if self.submitted or self.hints_used >= 3:
            return None
        level = self.hints_used + 1
        text = generator.bank_hint(self.question, level, self.ctx.language)
        if text is None:
            return None
        self.hints_used = level
        self._state(self.question.primary_skill).hint_level = level
        return level, text

    def reveal_reference(self) -> str:
        """Revealing before submitting is allowed, and produces no skill evidence (§2.9, §6.6)."""
        self.reference_revealed = True
        if not self.submitted:
            self.revealed_before_submit = True
        return self.question.text(self.ctx.language).reference_solution

    # ------------------------------------------------------------------ submit

    async def submit(self, answer, *, latency_ms: int | None = None, revision_count: int | None = None) -> PracticeOutcome:
        ctx, question = self.ctx, self.question
        self.submitted = True
        answer_text = answer if isinstance(answer, str) else answer.get("text") or answer.get("expression") or str(answer)
        check = checks.run_check(question.deterministic_check, answer) if question.deterministic_check else None
        self.check = check
        usage: list[UsageEvent] = []

        primary = ctx.skills[question.primary_skill]
        result = await evaluator.evaluate(
            ctx.provider, question_context=evaluator.question_block(question, ctx.language, primary),
            known_error_keys={e.key for e in question.common_errors}, language=ctx.language,
            difficulty=question.difficulty, answer=answer_text, check=check, hint_level=self.hints_used,
            glossary=ctx.glossary)
        self._record_usage(usage, "evaluate", result)
        if not result.ok:
            return PracticeOutcome(None, None, check, 0.0, None, None, None, None, None, usage=usage,
                                   flags=[*result.flags, "saved_without_evaluation"])

        outcome = await self._score_and_respond(result, answer_text, check, question.difficulty, latency_ms,
                                                revision_count, usage, is_follow_up=False)
        self.band, self.evaluation = outcome.band, outcome.evaluation
        return outcome

    async def submit_follow_up(self, answer_text: str, *, latency_ms: int | None = None) -> PracticeOutcome:
        if self._pending_follow_up is None:
            raise RuntimeError("there is no follow-up question to answer")
        ctx, pending = self.ctx, self._pending_follow_up
        usage: list[UsageEvent] = []
        primary = ctx.skills[self.question.primary_skill]
        state = self._state(primary.key)
        result = await evaluator.evaluate(
            ctx.provider, language=ctx.language, difficulty=self._follow_up_difficulty, answer=answer_text,
            question_context=evaluator.follow_up_block(pending.question_text, pending.expected_answer_outline,
                                                       primary, self._follow_up_difficulty),
            known_error_keys=set(), hint_level=state.hint_level, glossary=ctx.glossary)
        self._record_usage(usage, "evaluate", result)
        if not result.ok:
            self._pending_follow_up = None
            return PracticeOutcome(None, None, None, 0.0, None, None, None, None, None, usage=usage,
                                   flags=[*result.flags, "saved_without_evaluation"])
        return await self._score_and_respond(result, answer_text, None, self._follow_up_difficulty, latency_ms,
                                             None, usage, is_follow_up=True)

    # ------------------------------------------------------------------ internals

    def _state(self, key: str) -> SkillState:
        if key not in self.skill_states:
            self.skill_states[key] = SkillState(key=key)
        state = self.skill_states[key]
        if state.k is None or state.c is None:
            prior = scores.skill_prior(seniority=self.ctx.seniority, params=self.ctx.params)
            state.k = state.k if state.k is not None else prior.k
            state.c = state.c if state.c is not None else prior.c
        return state

    def _record_usage(self, usage: list[UsageEvent], action: str, result) -> None:
        if getattr(result, "model", ""):
            usage.append(UsageEvent(action, result.model, result.usage, result.latency_ms))

    async def _score_and_respond(self, result: EvaluationResult, answer_text: str, check: CheckResult | None,
                                 difficulty: int, latency_ms: int | None, revision_count: int | None,
                                 usage: list[UsageEvent], *, is_follow_up: bool) -> PracticeOutcome:
        ctx, question, params = self.ctx, self.question, self.ctx.params
        evaluation = scores.apply_check_result(result.evaluation, check, params)
        core = bool(set(evaluation.misconceptions) & question.core_misconception_keys)
        band = scores.classify_band(evaluation, core, params)
        self.misconceptions_hit = sorted(set(self.misconceptions_hit) | set(evaluation.misconceptions))

        primary_state = self._state(question.primary_skill)
        hint_level = primary_state.hint_level
        # a generated follow-up is new to everyone: it carries neither the bank question's
        # familiarity nor its exposure risk
        weight = scores.evidence_weight(
            self.evidence_mode, "new" if is_follow_up else self.familiarity, hint_level,
            "low" if is_follow_up else question.exposure_risk,
            revealed_before_submit=self.revealed_before_submit, params=params)

        # one metrics row per examined skill; secondary skills get evidence in proportion to their share
        links = [link for link in question.skills if link.primary] if is_follow_up else question.skills
        primary_share = next(link.weight for link in question.skills if link.primary)
        metrics = []
        for link in links:
            state = self._state(link.skill)
            skill_weight = round(min(weight, weight * link.weight / primary_share), 3)
            update = scores.update_scores(
                k_old=state.k, c_old=state.c, evaluation=evaluation, difficulty=difficulty,
                difficulty_ceiling=ctx.difficulty_ceiling, turns_on_skill=state.turns, hint_level=hint_level,
                latency_ms=latency_ms, revision_count=revision_count, weight=skill_weight, params=params)
            state.k, state.c = update.k_after, update.c_after
            scores.record_turn(state, difficulty=difficulty, band=band, evaluation=evaluation, hint_level=hint_level,
                               weight=skill_weight, core_misconception=core, archetype=question.archetype, params=params)
            catalog_skill = ctx.skills[link.skill]
            metrics.append({
                "mode": self.evidence_mode, "band": band.value, "subject_key": catalog_skill.subject, "skill_key": link.skill,
                "skill_source": "role", "skill_combined_weight": ctx.skill_weights.get(link.skill, link.weight),
                "skill_required_level": ctx.required_levels.get(link.skill, 2),
                "question_archetype": question.archetype.value, "difficulty_asked": difficulty,
                "evidence_weight": skill_weight, "check_passed": check.passed if check else None,
                "familiarity": "new" if is_follow_up else self.familiarity,
                "correctness": evaluation.correctness, "depth": evaluation.depth, "clarity": evaluation.clarity,
                "structure": evaluation.structure, "tradeoff_reasoning": evaluation.tradeoff_reasoning,
                "risk_awareness": evaluation.risk_awareness, "hedging_ratio": evaluation.hedging_ratio,
                "response_latency_ms": latency_ms, "revision_count": revision_count,
                "knowledge_score_before": update.k_before, "knowledge_score_after": update.k_after,
                "confidence_score_before": update.c_before, "confidence_score_after": update.c_after,
                "provisional_level_after": state.provisional_level, "hint_level": hint_level,
                "hint_delivered": hint_level > 0, "evaluator_model": result.model,
                "evaluator_version": result.prompt_version, "decision_engine_version": ENGINE_VERSION,
                "eval_latency_ms": result.latency_ms, "eval_flags": list(result.flags),
            })

        # what next: the skill controller, limited to two follow-ups and one escalation
        decision, follow_up_text = None, None
        if self.mode == "deep" and len(self.follow_up_turns) < MAX_FOLLOW_UPS and weight > 0:
            controller = skill_controller.decide(
                primary_state, band=band, confidence=primary_state.c, depth=evaluation.depth,
                plan_skill=self.plan_skill, difficulty_ceiling=ctx.difficulty_ceiling, params=params)
            wants_second_escalation = controller.action == Action.ESCALATE and self._escalated
            if not controller.resolved and not wants_second_escalation:
                self._escalated |= controller.action == Action.ESCALATE
                action, next_difficulty, next_hint = controller.action, controller.next_difficulty, controller.hint_level
                if action == Action.HINT:
                    # hints escalate one level at a time, counting the ones already taken before submitting
                    if self.hints_used >= params.controller.max_hint_level:
                        action, next_hint = Action.STEP_BACK, 0
                        next_difficulty = max(self.plan_skill.min_difficulty, difficulty - params.controller.step_back_delta)
                    else:
                        next_hint = self.hints_used + 1
                        self.hints_used = next_hint
                    primary_state.hint_level = next_hint
                decision = Decision(
                    action=action, reason_code=controller.reason_code, target_subject=question.subject,
                    target_skill=controller.target_skill or question.primary_skill,
                    target_difficulty=next_difficulty, target_archetype=question.archetype,
                    probe_focus="; ".join(evaluation.key_points_missed[:2]) or None,
                    deliver_hint=action == Action.HINT, hint_level=next_hint)
                generated = await generator.generate(
                    ctx.provider, decision, language=ctx.language,
                    skill=ctx.skills.get(decision.target_skill), question=question,
                    last_question=self._pending_follow_up.question_text if is_follow_up else question.text(ctx.language).prompt,
                    last_answer_summary=evaluation.one_line_summary, glossary=ctx.glossary,
                    previous_questions=[question.text(ctx.language).prompt, *[t["question"] for t in self.follow_up_turns]])
                self._record_usage(usage, "generate", generated)
                self._pending_follow_up = generated.question
                self._follow_up_difficulty = next_difficulty or difficulty
                follow_up_text = generated.question.question_text
                metrics[0]["decision_action"] = action.value
                metrics[0]["decision_reason_code"] = controller.reason_code
                metrics[0]["difficulty_next"] = next_difficulty
            else:
                metrics[0]["decision_reason_code"] = controller.reason_code
        if follow_up_text is None:
            self._pending_follow_up = None

        if is_follow_up:
            self.follow_up_turns[-1].update({"answer": answer_text, "evaluation": evaluation.model_dump(),
                                             "band": band.value})
        if follow_up_text is not None:
            self.follow_up_turns.append({"question": follow_up_text, "generated": True,
                                         "action": decision.action.value, "difficulty": self._follow_up_difficulty})

        # the feedback card belongs to the main question; follow-ups get the tip and the next question only
        card = None
        if not is_follow_up:
            built = await feedback.build_card(
                ctx.provider, question=question, evaluation=evaluation, band=band, answer=answer_text, check=check,
                language=ctx.language, skill_label=ctx.skills[question.primary_skill].label, glossary=ctx.glossary)
            self._record_usage(usage, "feedback", built)
            card = built.card

        tip_text, tip_key = await self._tip(evaluation, band, hint_level, check, usage)
        flags = list(result.flags)
        if self.revealed_before_submit:
            flags.append("revealed_before_submit_no_evidence")
        return PracticeOutcome(band, evaluation, check, weight, card, tip_text, tip_key, follow_up_text, decision,
                               metrics=metrics, usage=usage, flags=flags)

    async def _tip(self, evaluation: Evaluation, band: Band, hint_level: int, check: CheckResult | None,
                   usage: list[UsageEvent]) -> tuple[str | None, str | None]:
        ctx = self.ctx
        if not ctx.tips:
            return None, None
        state = self._state(self.question.primary_skill)
        signals = tips.signals_from(evaluation, band=band, archetype=self.question.archetype.value,
                                    hint_level=hint_level, confidence=state.c, self_confidence=self.self_confidence,
                                    mode=self.mode, check_passed=check.passed if check else None)
        # tips named by a matched common error come first; then the rule-matched library
        named = [e.tip_key for e in self.question.common_errors if e.key in evaluation.misconceptions and e.tip_key]
        pool = [t for t in ctx.tips if t.key in named] or ctx.tips
        turn = len(self.follow_up_turns)
        choice = tips.select_tip(pool, signals, turn_index=turn, last_delivered_turn=self._tip_turns,
                                 skill_key=self.question.primary_skill, role_family=ctx.role_family,
                                 timing="post_session")
        if choice is None and named:
            forced = next((t for t in ctx.tips if t.key in named), None)
            choice = tips.TipChoice(forced, "post_session", float(forced.severity)) if forced else None
        if choice is None:
            return None, None
        self._tip_turns[choice.tip.key] = turn
        placeholders = {"missed_point": (evaluation.key_points_missed or [""])[0],
                        "skill_label": ctx.skills[self.question.primary_skill].label}
        text = await tips.compose(ctx.provider if ctx.polish_tips else None, choice, language=ctx.language,
                                  placeholders=placeholders)
        return text, choice.tip.key

    # ------------------------------------------------------------------ what to persist

    def attempt_row(self, *, duration_ms: int | None = None) -> dict:
        """The fields of public.attempt this engine owns (Data_Models §14.2)."""
        return {
            "question_key": self.question.key, "question_version": self.question.version, "mode": self.mode,
            "practice_language": self.ctx.language, "self_confidence_before": self.self_confidence,
            "check_result": self.check.model_dump() if self.check else None,
            "evaluation": self.evaluation.model_dump() if self.evaluation else None,
            "band": self.band.value if self.band else None, "hints_used": self.hints_used,
            "reference_revealed": self.reference_revealed, "revealed_before_submit": self.revealed_before_submit,
            "follow_up_turns": self.follow_up_turns, "misconceptions_hit": self.misconceptions_hit,
            "familiarity": self.familiarity, "duration_ms": duration_ms,
        }
