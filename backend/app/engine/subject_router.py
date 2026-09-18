"""Layer 2: the Subject Router (AI_Engine_Spec §4).

Runs after every turn. Keeps subject state current and, when the Skill Controller
resolves a skill, chooses the next subject, the next skill and the entry
difficulty. This is how earlier answers shape which subjects come next and how
hard they start.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.engine import skill_controller
from app.engine.params import DEFAULT_PARAMS, EngineParams
from app.engine.scores import clamp, momentum, round_half_up
from app.engine.skill_controller import ControllerResult
from app.schemas.engine import (
    IMPORTANCE_RANK,
    Action,
    Archetype,
    AssessmentMode,
    Band,
    Bridge,
    Decision,
    Importance,
    ObservedState,
    PlanSkill,
    SessionState,
    SkillState,
    SkillStatus,
    SubjectState,
    SubjectStatus,
)

# ----------------------------------------------------------------------------- setup


def init_session_state(plan: list[PlanSkill], *, seniority: str, baseline_difficulty: int,
                       difficulty_ceiling: int, planned_duration_min: float,
                       priors: dict[str, tuple[float, float]] | None = None,
                       params: EngineParams = DEFAULT_PARAMS) -> SessionState:
    """Build the live state from the frozen session skill plan (§4.1)."""
    state = SessionState(seniority=seniority, baseline_difficulty=baseline_difficulty,
                         difficulty_ceiling=difficulty_ceiling, planned_duration_min=planned_duration_min)
    priors = priors or {}
    for skill in plan:
        if skill.assessment_mode == AssessmentMode.OBSERVED:
            state.observed_state[skill.key] = ObservedState(key=skill.key)
            continue
        k, c = priors.get(skill.key, (None, None))
        state.skill_state[skill.key] = SkillState(key=skill.key, k=k, c=c,
                                                  budget=params.controller.struggle_budget_per_skill)
        state.skill_turns_planned[skill.key] = skill.planned_turns

    for subject_key in dict.fromkeys(s.subject for s in plan):
        members = [s for s in plan if s.subject == subject_key]
        questioned = [s for s in members if _examined(s)]
        weight = sum(s.combined_weight for s in members)
        required = (sum(s.required_level * s.combined_weight for s in members) / weight) if weight else 1.0
        turns = sum(s.planned_turns for s in questioned)
        state.subject_state[subject_key] = SubjectState(
            key=subject_key, weight=round(weight, 4),
            importance=max((s.importance for s in members), key=lambda i: IMPORTANCE_RANK[i]),
            required_level=round(required, 2), turns_planned=turns, turns_planned_original=turns,
            skills_planned=len(questioned),
            status=SubjectStatus.UNTOUCHED if questioned else SubjectStatus.DONE,
        )
    return state


def _examined(skill: PlanSkill) -> bool:
    """Questioned skills that got turns. Zero-turn, non-core skills are 'not assessed this session' (§6.3)."""
    return skill.assessment_mode == AssessmentMode.QUESTIONED and (
        skill.planned_turns > 0 or skill.importance == Importance.CORE)


# ----------------------------------------------------------------------------- §4.2 subject state


def update_subject_state(state: SessionState, plan: list[PlanSkill], subject_key: str, band: Band,
                         params: EngineParams = DEFAULT_PARAMS) -> tuple[SubjectStatus, SubjectStatus]:
    """Refresh one subject after a turn in it. Returns (status_before, status_after)."""
    subject = state.subject_state[subject_key]
    before = subject.status
    subject.turns_used += 1
    subject.recent_bands.append(band)
    subject.weak_answers += int(band == Band.WEAK)
    subject.momentum = momentum(subject.recent_bands, params.router.subject_momentum_window)
    state.recent_bands.append(band)
    _recompute_subject(state, plan, subject, params)
    return before, subject.status


def _recompute_subject(state: SessionState, plan: list[PlanSkill], subject: SubjectState,
                       params: EngineParams) -> None:
    members = [s for s in plan if s.subject == subject.key and _examined(s)]
    touched = [(s, state.skill_state[s.key]) for s in members if state.skill_state[s.key].turns > 0]
    weight = sum(s.combined_weight for s, _ in touched)
    if weight > 0:
        subject.k = round(sum((st.k or 0.0) * s.combined_weight for s, st in touched) / weight, 2)
        subject.c = round(sum((st.c or 0.0) * s.combined_weight for s, st in touched) / weight, 2)
        subject.level = round(sum((st.provisional_level or 1) * s.combined_weight for s, st in touched) / weight, 2)
    resolved = [(s, state.skill_state[s.key]) for s in members if state.skill_state[s.key].resolved]
    subject.skills_resolved = len(resolved)
    subject.status = _subject_status(subject, resolved, params)


def _subject_status(subject: SubjectState, resolved: list[tuple[PlanSkill, SkillState]],
                    params: EngineParams) -> SubjectStatus:
    r = params.router
    if subject.closed_early or (subject.skills_planned and subject.skills_resolved >= subject.skills_planned):
        return SubjectStatus.DONE
    if subject.turns_used == 0:
        return SubjectStatus.UNTOUCHED
    level = subject.level if subject.level is not None else 0.0
    if len(resolved) >= 2:
        if level >= subject.required_level + r.strong_level_margin and subject.weak_answers == 0:
            return SubjectStatus.STRONG
        meets = [(st.provisional_level or 1) >= s.required_level for s, st in resolved]
        if any(meets) and not all(meets):
            return SubjectStatus.MIXED
    if (subject.turns_used >= 2 and level <= subject.required_level - r.weak_level_margin) or subject.weak_answers >= 2:
        return SubjectStatus.WEAK
    return SubjectStatus.EXPLORING


def session_momentum(state: SessionState, params: EngineParams = DEFAULT_PARAMS) -> float:
    return momentum(state.recent_bands, params.router.session_momentum_window)


# ----------------------------------------------------------------------------- §4.6 rebalancing


def rebalance(state: SessionState, plan: list[PlanSkill], subject_key: str,
              params: EngineParams = DEFAULT_PARAMS) -> list[str]:
    """Adjust the remaining turn allocation after a skill resolves. Returns reason codes."""
    r = params.router
    subject = state.subject_state[subject_key]
    codes: list[str] = []
    members = [s for s in plan if s.subject == subject_key and _examined(s)]
    unresolved = [s for s in members if not state.skill_state[s.key].resolved]

    # close early: every core skill resolved at required + 1 or better
    core = [s for s in members if s.importance == Importance.CORE]
    if unresolved and core and all(
        state.skill_state[s.key].resolved
        and (state.skill_state[s.key].provisional_level or 0) >= s.required_level + 1 for s in core
    ):
        subject.closed_early = True
        codes.append("subject_closed_early")
    # close early: the weak cap is used up and every skill has had a turn
    cap = round_half_up(subject.turns_planned_original * r.weak_cap_factor)
    if (unresolved and subject.status == SubjectStatus.WEAK and subject.turns_used >= cap
            and all(state.skill_state[s.key].turns >= 1 for s in members)):
        subject.closed_early = True
        codes.append("subject_closed_early")
    if subject.closed_early:
        subject.status = SubjectStatus.DONE

    if subject.status == SubjectStatus.DONE:
        released = sum(max(0, state.skill_turns_planned.get(s.key, 0) - state.skill_state[s.key].turns)
                       for s in members)
        for s in members:
            state.skill_turns_planned[s.key] = state.skill_state[s.key].turns
        _release(state, plan, released, exclude_subject=subject_key)
    elif subject.status == SubjectStatus.STRONG and subject.rebalanced_for != SubjectStatus.STRONG:
        released = 0
        for s in unresolved:
            remaining = max(0, state.skill_turns_planned.get(s.key, 0) - state.skill_state[s.key].turns)
            kept = round_half_up(remaining * r.strong_turn_factor)
            if s.importance == Importance.CORE:
                kept = max(kept, 1)
            released += remaining - kept
            state.skill_turns_planned[s.key] = state.skill_state[s.key].turns + kept
        _release(state, plan, released, exclude_subject=subject_key)
        subject.rebalanced_for = SubjectStatus.STRONG
        codes.append("rebalance_strong_release")
    elif subject.status == SubjectStatus.WEAK and subject.rebalanced_for != SubjectStatus.WEAK:
        room = max(0, cap - sum(state.skill_turns_planned.get(s.key, 0) for s in members))
        for s in unresolved:
            if room <= 0:
                break
            state.skill_turns_planned[s.key] = state.skill_turns_planned.get(s.key, 0) + 1
            room -= 1
        subject.rebalanced_for = SubjectStatus.WEAK
        codes.append("rebalance_weak_extend")

    subject.turns_planned = sum(state.skill_turns_planned.get(s.key, 0) for s in members)
    return codes


def _release(state: SessionState, plan: list[PlanSkill], turns: int, exclude_subject: str) -> None:
    """Released turns go to unresolved core skills first, by weight, then to important skills."""
    if turns <= 0:
        return
    state.turn_pool_released += turns
    candidates = [s for s in plan if s.subject != exclude_subject and _examined(s)
                  and not state.skill_state[s.key].resolved
                  and s.importance in (Importance.CORE, Importance.IMPORTANT)]
    candidates.sort(key=lambda s: (s.importance != Importance.CORE, -s.combined_weight))
    index = 0
    while turns > 0 and candidates:
        skill = candidates[index % len(candidates)]
        state.skill_turns_planned[skill.key] = state.skill_turns_planned.get(skill.key, 0) + 1
        turns -= 1
        index += 1
    for subject in state.subject_state.values():
        subject.turns_planned = sum(state.skill_turns_planned.get(s.key, 0)
                                    for s in plan if s.subject == subject.key and _examined(s))


# ----------------------------------------------------------------------------- §4.3 next subject


def _open_subjects(state: SessionState) -> list[SubjectState]:
    return [s for s in state.subject_state.values() if s.status != SubjectStatus.DONE]


def fatigue_active(state: SessionState, params: EngineParams = DEFAULT_PARAMS) -> bool:
    """The last two subjects visited both ended on momentum <= -0.5."""
    visited = state.subjects_visited_order[-2:]
    if len(visited) < 2 or visited[0] == visited[1]:
        return False
    for key in visited:
        subject = state.subject_state[key]
        ending = subject.final_momentum if subject.final_momentum is not None else subject.momentum
        if ending > params.router.fatigue_momentum:
            return False
    return True


def subject_score(state: SessionState, plan: list[PlanSkill], subject: SubjectState, *, fatigue: bool,
                  params: EngineParams = DEFAULT_PARAMS) -> float:
    r = params.router
    unresolved = [s for s in plan if s.subject == subject.key and _examined(s)
                  and not state.skill_state[s.key].resolved]
    # §4.3 lists {weak, mixed, untouched}. EXPLORING is included because the §4.10 worked session
    # (turn 2: stay in SystemVerilog rather than open untouched, core UVM) only holds if a core
    # subject that is still being explored keeps its "open questions" bonus.
    core_gap = (subject.importance == Importance.CORE
                and subject.status in (SubjectStatus.WEAK, SubjectStatus.MIXED, SubjectStatus.UNTOUCHED,
                                       SubjectStatus.EXPLORING))
    stay = subject.key == state.current_subject and subject.coverage < 1
    focus = any(s.in_user_focus for s in unresolved)
    fatigued = fatigue and subject.status in (SubjectStatus.UNTOUCHED, SubjectStatus.WEAK)
    recently_left = (subject.key != state.current_subject and subject.left_at_turn is not None
                     and state.turn_index - subject.left_at_turn <= r.recent_turns_window)
    return round(
        r.w_weight * subject.weight
        + r.w_uncover * (1 - subject.coverage)
        + r.w_core_gap * core_gap
        + r.w_stay * stay
        + r.w_focus * focus
        - r.w_strong * (subject.status == SubjectStatus.STRONG)
        - r.w_fatigue * fatigued
        - r.w_recent * recently_left, 4)


@dataclass(frozen=True)
class SubjectChoice:
    subject: str | None
    reason_code: str
    skill: str | None = None           # set by the ending override, which picks a skill directly


def choose_subject(state: SessionState, plan: list[PlanSkill], *,
                   subject_prior_k: dict[str, float] | None = None,
                   params: EngineParams = DEFAULT_PARAMS) -> SubjectChoice:
    open_subjects = _open_subjects(state)
    if not open_subjects:
        return SubjectChoice(None, "plan_complete")

    # ending override: under six minutes left
    if state.remaining_min < params.router.ending_override_minutes:
        core = [s for s in plan if _examined(s) and s.importance == Importance.CORE
                and not state.skill_state[s.key].resolved
                and state.subject_state[s.subject].status != SubjectStatus.DONE]
        if core:
            best = min(core, key=lambda s: s.priority_rank)
            return SubjectChoice(best.subject, "ending_override", skill=best.key)
        strong = [s for s in open_subjects if s.status == SubjectStatus.STRONG]
        if strong:
            return SubjectChoice(max(strong, key=lambda s: s.weight).key, "ending_override")

    # fatigue override: a success before the next hard area
    fatigue = fatigue_active(state, params)
    if fatigue:
        strong = [s for s in open_subjects if s.status == SubjectStatus.STRONG]
        if strong:
            return SubjectChoice(max(strong, key=lambda s: s.weight).key, "fatigue_override")
        untouched = [s for s in open_subjects if s.status == SubjectStatus.UNTOUCHED]
        if untouched:
            prior = subject_prior_k or {}
            return SubjectChoice(max(untouched, key=lambda s: (prior.get(s.key, 0.0), s.weight)).key,
                                 "fatigue_override")

    scored = sorted(open_subjects, key=lambda s: (-subject_score(state, plan, s, fatigue=fatigue, params=params), s.key))
    best = scored[0]
    if best.key == state.current_subject:
        reason = "subject_continue"
    elif best.importance == Importance.CORE and best.status in (SubjectStatus.WEAK, SubjectStatus.MIXED,
                                                                  SubjectStatus.UNTOUCHED):
        reason = "subject_selected_core_gap"
    else:
        reason = "subject_selected_by_score"
    return SubjectChoice(best.key, reason)


# ----------------------------------------------------------------------------- §4.4 next skill


def choose_skill(state: SessionState, plan: list[PlanSkill], subject_key: str,
                 params: EngineParams = DEFAULT_PARAMS) -> PlanSkill | None:
    r = params.router
    subject = state.subject_state[subject_key]
    by_key = {s.key: s for s in plan}
    candidates = [s for s in plan if s.subject == subject_key and _examined(s)
                  and not state.skill_state[s.key].resolved]
    if not candidates:
        return None

    def priority(skill: PlanSkill) -> float:
        prerequisites = [p for p in skill.prerequisites if p in state.skill_state]
        all_resolved = all(state.skill_state[p].resolved for p in prerequisites)
        any_unresolved = any(not state.skill_state[p].resolved for p in prerequisites)
        return (skill.combined_weight
                + r.skill_core_bonus * (skill.importance == Importance.CORE)
                + r.skill_focus_bonus * skill.in_user_focus
                + r.skill_prereq_resolved_bonus * all_resolved
                - r.skill_prereq_unresolved_penalty * (any_unresolved and subject.status == SubjectStatus.WEAK))

    best = max(candidates, key=lambda s: (priority(s), -s.priority_rank))
    # foundation first: never open a skill while one of its planned prerequisites is still open
    open_prerequisites = [by_key[p] for p in best.prerequisites
                          if p in by_key and by_key[p] in candidates]
    if open_prerequisites:
        return max(open_prerequisites, key=lambda s: (priority(s), -s.priority_rank))
    return best


# ----------------------------------------------------------------------------- §4.5 entry difficulty


def entry_difficulty(state: SessionState, plan: list[PlanSkill], skill: PlanSkill,
                     params: EngineParams = DEFAULT_PARAMS) -> tuple[int, dict[str, int]]:
    r = params.router
    subject = state.subject_state[skill.subject]
    by_key = {s.key: s for s in plan}

    if subject.status == SubjectStatus.STRONG:
        subject_adjust = r.entry_strong_adjust
    elif subject.status == SubjectStatus.WEAK:
        subject_adjust = r.entry_weak_adjust
    elif subject.k is not None and subject.k >= r.entry_high_k_threshold:
        subject_adjust = r.entry_high_k_adjust
    elif subject.status == SubjectStatus.MIXED and subject.k is not None and subject.k < r.entry_mixed_low_threshold:
        subject_adjust = r.entry_mixed_low_adjust
    else:
        subject_adjust = 0

    resolved = [(by_key[p], state.skill_state[p]) for p in skill.prerequisites
                if p in by_key and p in state.skill_state and state.skill_state[p].resolved]
    prerequisite_adjust = 0
    if resolved:
        if any((st.provisional_level or 0) < s.required_level for s, st in resolved):
            prerequisite_adjust = -1
        elif len(resolved) == len([p for p in skill.prerequisites if p in by_key]):
            prerequisite_adjust = 1

    m = session_momentum(state, params)
    momentum_adjust = 1 if m >= r.entry_momentum_threshold else -1 if m <= -r.entry_momentum_threshold else 0

    adjust = int(clamp(subject_adjust + prerequisite_adjust + momentum_adjust,
                       -r.entry_max_below_baseline, r.entry_max_above_baseline))
    top = min(skill.max_difficulty, state.difficulty_ceiling)
    entry = int(clamp(state.baseline_difficulty + adjust, min(skill.min_difficulty, top), top))
    return entry, {"baseline": state.baseline_difficulty, "subject_adjust": subject_adjust,
                   "prerequisite_adjust": prerequisite_adjust, "momentum_adjust": momentum_adjust}


# ----------------------------------------------------------------------------- §4.7 and §4.8


def observed_skills_short_on_evidence(state: SessionState, plan: list[PlanSkill],
                                      params: EngineParams = DEFAULT_PARAMS) -> list[str]:
    """Observed core skills with too few relevant turns once the session is past halfway."""
    if state.elapsed_ms < state.planned_duration_min * 60_000 / 2:
        return []
    return [s.key for s in plan
            if s.assessment_mode == AssessmentMode.OBSERVED and s.importance == Importance.CORE
            and state.observed_state[s.key].n_relevant < params.router.observed_core_min_relevant_turns]


def choose_bridge(state: SessionState, target: SubjectState, *, fatigue_override: bool,
                  last_subject: bool) -> Bridge | None:
    previous = state.subject_state.get(state.current_subject) if state.current_subject else None
    if last_subject:
        return Bridge.LAST_AREA
    if fatigue_override:
        return Bridge.CLEAN_TOPIC
    if target.status == SubjectStatus.WEAK or (target.turns_used > 0 and target.weak_answers > 0):
        return Bridge.FRESH_START
    if previous and previous.status in (SubjectStatus.STRONG, SubjectStatus.DONE) and previous.weak_answers == 0 \
            and target.status == SubjectStatus.UNTOUCHED:
        return Bridge.STRENGTH_REFERENCE
    return None


# ----------------------------------------------------------------------------- §4.9 the decision flow


def first_decision(state: SessionState, plan: list[PlanSkill], *,
                   subject_prior_k: dict[str, float] | None = None,
                   params: EngineParams = DEFAULT_PARAMS) -> Decision:
    """Open the session: choose the first subject and skill."""
    return _enter_next(state, plan, rebalance_codes=[], subject_prior_k=subject_prior_k, params=params)


def route(state: SessionState, plan: list[PlanSkill], result: ControllerResult, *,
          probe_focus: str | None = None, subject_prior_k: dict[str, float] | None = None,
          params: EngineParams = DEFAULT_PARAMS) -> Decision:
    """Turn the Skill Controller's result into the next authoritative decision."""
    invite = observed_skills_short_on_evidence(state, plan, params)

    # the §4.9 ending check runs when a skill resolves; the clock itself is a hard stop
    if state.remaining_min <= 0:
        state.recent_actions.append(Action.END)
        return Decision(action=Action.END, reason_code="time_up")

    if not result.resolved:
        by_key = {s.key: s for s in plan}
        current = by_key[state.current_skill]
        archetype = result.target_archetype or (Archetype.DESIGN if invite else Archetype.CONCEPTUAL)
        state.current_difficulty = result.next_difficulty
        state.recent_actions.append(result.action)
        return Decision(
            action=result.action, reason_code=result.reason_code, target_subject=current.subject,
            target_skill=result.target_skill or current.key, target_difficulty=result.next_difficulty,
            target_archetype=archetype, subject_switch=False,
            probe_focus=probe_focus if result.action in (Action.HOLD, Action.HINT) else None,
            invite_observed_skills=invite, deliver_hint=result.action == Action.HINT,
            hint_level=result.hint_level,
        )

    codes: list[str] = []
    if state.current_subject:
        # the subject's status was computed before the controller resolved this skill;
        # refresh it so rebalancing and the next choice see the resolution
        _recompute_subject(state, plan, state.subject_state[state.current_subject], params)
        codes = rebalance(state, plan, state.current_subject, params)
    if state.remaining_min < params.router.end_session_minutes:
        state.recent_actions.append(Action.END)
        return Decision(action=Action.END, reason_code="time_up", rebalance_codes=codes)
    return _enter_next(state, plan, rebalance_codes=codes, subject_prior_k=subject_prior_k, params=params,
                       invite=invite)


def _enter_next(state: SessionState, plan: list[PlanSkill], *, rebalance_codes: list[str],
                subject_prior_k: dict[str, float] | None, params: EngineParams,
                invite: list[str] | None = None) -> Decision:
    by_key = {s.key: s for s in plan}
    while True:
        choice = choose_subject(state, plan, subject_prior_k=subject_prior_k, params=params)
        if choice.subject is None:
            state.recent_actions.append(Action.END)
            return Decision(action=Action.END, reason_code=choice.reason_code, rebalance_codes=rebalance_codes)
        skill = by_key[choice.skill] if choice.skill else choose_skill(state, plan, choice.subject, params)
        if skill is not None:
            break
        state.subject_state[choice.subject].status = SubjectStatus.DONE     # nothing left to ask here

    target = state.subject_state[skill.subject]
    switching = skill.subject != state.current_subject
    open_after = [s for s in _open_subjects(state) if s.key != skill.subject]
    last_subject = switching and not open_after and state.current_subject is not None
    bridge = choose_bridge(state, target, fatigue_override=choice.reason_code == "fatigue_override",
                           last_subject=last_subject or choice.reason_code == "ending_override") if switching else None
    bridge_from = state.current_skill if bridge == Bridge.STRENGTH_REFERENCE else None

    difficulty, reason = entry_difficulty(state, plan, skill, params)

    if switching and state.current_subject:
        previous = state.subject_state[state.current_subject]
        previous.left_at_turn = state.turn_index
        previous.final_momentum = previous.momentum
    if switching:
        state.subjects_visited_order.append(skill.subject)
    state.current_subject = skill.subject
    state.current_skill = skill.key
    state.current_difficulty = difficulty
    skill_controller.enter_skill(state.skill_state[skill.key], difficulty, params)
    state.recent_actions.append(Action.ENTER_SKILL)

    invite = invite or []
    return Decision(
        action=Action.ENTER_SKILL, reason_code=choice.reason_code, target_subject=skill.subject,
        target_skill=skill.key, target_difficulty=difficulty,
        target_archetype=Archetype.DESIGN if invite else Archetype.CONCEPTUAL,
        subject_switch=switching, entry_difficulty_reason=reason, bridge=bridge, bridge_from_skill=bridge_from,
        invite_observed_skills=invite, rebalance_codes=rebalance_codes,
    )


def skill_status_label(status: SkillStatus) -> str:
    return status.value
