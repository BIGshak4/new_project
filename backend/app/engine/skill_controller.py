"""Layer 1: the Skill Controller (AI_Engine_Spec §3).

Decides, inside one skill: go harder, hold, hint, step back, or hand the skill to
the Subject Router as resolved. One function, one table, no LLM.

Reading the transition table against the §4.10 worked session fixed three details
the table leaves implicit:
  * a PARTIAL right after an escalation counts as the first PARTIAL at that
    difficulty (turns 4-5: PARTIAL, PARTIAL -> resolved);
  * a PARTIAL that recovers from a hint also counts (turns 8-9);
  * with no budget left, a WEAK answer steps back from any state (turn 15).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.engine.params import DEFAULT_PARAMS, EngineParams
from app.engine.scores import level_from_difficulty
from app.schemas.engine import Action, Archetype, Band, PlanSkill, SkillState, SkillStatus


@dataclass(frozen=True)
class ControllerResult:
    action: Action | None              # None when the skill is resolved and the router takes over
    reason_code: str
    resolved: bool
    next_difficulty: int | None = None
    hint_level: int = 0
    target_skill: str | None = None    # differs from the current skill only on a step back to a prerequisite
    target_archetype: Archetype | None = None
    recovered_after_hint: bool | None = None


def enter_skill(state: SkillState, difficulty: int, params: EngineParams = DEFAULT_PARAMS) -> None:
    """Called by the router when it opens a skill."""
    state.status = SkillStatus.ENTERING
    state.current_difficulty = difficulty
    state.hint_level = 0
    state.partial_count = 0
    if state.turns == 0:
        state.budget = params.controller.struggle_budget_per_skill


def decide(state: SkillState, *, band: Band, confidence: float, depth: float, plan_skill: PlanSkill,
           difficulty_ceiling: int, catalog_min_difficulty: dict[str, int] | None = None,
           params: EngineParams = DEFAULT_PARAMS) -> ControllerResult:
    """Apply the §3.3 transition table. Mutates `state` to the next controller state."""
    p = params.controller
    difficulty = state.current_difficulty or plan_skill.min_difficulty
    top = min(plan_skill.max_difficulty, difficulty_ceiling)
    status = SkillStatus.HOLD_ZONE if state.status in (SkillStatus.ENTERING, SkillStatus.UNTOUCHED) else state.status

    # STEPPING_BACK: one fundamental question settles it, whatever the band
    if status == SkillStatus.STEPPING_BACK:
        return _resolve(state, SkillStatus.BASELINE_MAPPED, "baseline_mapped")

    # HINTING
    if status in (SkillStatus.HINTING, SkillStatus.STRUGGLING):
        if band in (Band.STRONG, Band.PARTIAL):
            state.status = SkillStatus.HOLD_ZONE
            state.hint_level = 0
            state.partial_count += 1 if band == Band.PARTIAL else 0
            if band == Band.STRONG:
                state.partial_count = 0
            # recovery earns a HOLD, never an escalation (§6.7)
            return ControllerResult(Action.HOLD, "recovered_after_hint", False, next_difficulty=difficulty,
                                    recovered_after_hint=True)
        if state.budget > 0:
            state.budget -= 1
            state.hint_level = min(state.hint_level + 1, p.max_hint_level)
            state.status = SkillStatus.HINTING
            return ControllerResult(Action.HINT, "escalate_hint", False, next_difficulty=difficulty,
                                    hint_level=state.hint_level, recovered_after_hint=False)
        return _step_back(state, plan_skill, difficulty, catalog_min_difficulty, params, recovered=False)

    # HOLD_ZONE and ESCALATING
    if band == Band.STRONG:
        state.partial_count = 0
        if status == SkillStatus.ESCALATING or difficulty >= top:
            if difficulty >= top:
                return _resolve(state, SkillStatus.CEILING_FOUND, "ceiling_reached")
            if status == SkillStatus.ESCALATING and level_from_difficulty(difficulty) >= plan_skill.required_level + 1:
                return _resolve(state, SkillStatus.CEILING_FOUND, "requirement_exceeded")
            state.status = SkillStatus.ESCALATING
            state.current_difficulty = min(difficulty + 1, top)
            return ControllerResult(Action.ESCALATE, "sustained_strength", False,
                                    next_difficulty=state.current_difficulty)
        step = 2 if confidence >= p.double_escalate_confidence and depth >= p.double_escalate_depth else 1
        state.status = SkillStatus.ESCALATING
        state.current_difficulty = min(difficulty + step, top)
        return ControllerResult(Action.ESCALATE, "strong_answer", False, next_difficulty=state.current_difficulty)

    if band == Band.PARTIAL:
        state.partial_count += 1
        if status == SkillStatus.ESCALATING:
            state.status = SkillStatus.HOLD_ZONE
            return ControllerResult(Action.HOLD, "probe_gap_after_escalation", False, next_difficulty=difficulty)
        if state.partial_count <= 1:
            state.status = SkillStatus.HOLD_ZONE
            return ControllerResult(Action.HOLD, "probe_gap", False, next_difficulty=difficulty)
        if confidence >= p.soft_ceiling_confidence:
            return _resolve(state, SkillStatus.CEILING_FOUND, "ceiling_found_soft")
        if state.budget > 0:
            return _hint(state, difficulty, "partial_low_confidence")
        return _step_back(state, plan_skill, difficulty, catalog_min_difficulty, params)

    # WEAK
    if state.budget > 0:
        return _hint(state, difficulty, "weak_answer_budget_available")
    return _step_back(state, plan_skill, difficulty, catalog_min_difficulty, params)


def request_hint(state: SkillState, params: EngineParams = DEFAULT_PARAMS) -> ControllerResult | None:
    """Coach Mode: the user asks for a hint. Starts at level 1 and consumes budget (§3.3, §6.3)."""
    if state.budget <= 0 or state.resolved:
        return None
    state.budget -= 1
    state.hint_level = min(state.hint_level + 1, params.controller.max_hint_level)
    state.status = SkillStatus.HINTING
    return ControllerResult(Action.HINT, "user_requested_hint", False, next_difficulty=state.current_difficulty,
                            hint_level=state.hint_level)


# ----------------------------------------------------------------------------- helpers


def _resolve(state: SkillState, status: SkillStatus, reason: str) -> ControllerResult:
    state.status = status
    state.resolved_reason = reason
    state.hint_level = 0
    return ControllerResult(None, reason, True)


def _hint(state: SkillState, difficulty: int, reason: str) -> ControllerResult:
    state.budget -= 1
    state.hint_level = 1
    state.status = SkillStatus.HINTING
    return ControllerResult(Action.HINT, reason, False, next_difficulty=difficulty, hint_level=1)


def _step_back(state: SkillState, plan_skill: PlanSkill, difficulty: int,
               catalog_min_difficulty: dict[str, int] | None, params: EngineParams,
               recovered: bool | None = None) -> ControllerResult:
    """§3.4: to a prerequisite at its minimum + 1 if one exists, else same skill two levels down."""
    state.status = SkillStatus.STEPPING_BACK
    state.hint_level = 0
    state.partial_count = 0
    prerequisite = plan_skill.prerequisites[0] if plan_skill.prerequisites else None
    if prerequisite and catalog_min_difficulty and prerequisite in catalog_min_difficulty:
        target = catalog_min_difficulty[prerequisite] + 1
        state.current_difficulty = target
        return ControllerResult(Action.STEP_BACK, "budget_exhausted", False, next_difficulty=target,
                                target_skill=prerequisite, target_archetype=Archetype.CONCEPTUAL,
                                recovered_after_hint=recovered)
    target = max(plan_skill.min_difficulty, difficulty - params.controller.step_back_delta)
    state.current_difficulty = target
    return ControllerResult(Action.STEP_BACK, "budget_exhausted", False, next_difficulty=target,
                            target_skill=state.key, target_archetype=Archetype.CONCEPTUAL,
                            recovered_after_hint=recovered)
