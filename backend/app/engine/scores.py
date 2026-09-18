"""Scores, levels and evidence (AI_Engine_Spec §2, §3.1).

Every function is pure: numbers in, numbers out. Thresholds live in params.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.engine.params import DEFAULT_PARAMS, EngineParams
from app.schemas.engine import (
    Archetype,
    Band,
    CheckResult,
    Evaluation,
    EvidenceStatus,
    ObservedState,
    SkillState,
    TurnRecord,
)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def round_half_up(value: float) -> int:
    """Python's round() uses banker's rounding; levels and turn counts must not."""
    return int(value + 0.5) if value >= 0 else -int(-value + 0.5)


# ----------------------------------------------------------------------------- §2.3 check authority


def apply_check_result(evaluation: Evaluation, check: CheckResult | None,
                       params: EngineParams = DEFAULT_PARAMS) -> Evaluation:
    """A failed check caps correctness at 0.4; a pass raises the floor to 0.6, never to 1.0."""
    if check is None or check.passed is None:
        return evaluation
    p = params.scores
    correctness = evaluation.correctness
    if check.passed:
        correctness = max(correctness, p.check_pass_correctness_floor)
    else:
        correctness = min(correctness, p.check_fail_correctness_cap)
    return evaluation.model_copy(update={"correctness": correctness})


# ----------------------------------------------------------------------------- §2.8 company emphasis

DIMENSION_FOR_OBSERVED_SKILL = {
    "risk_awareness": "risk_awareness",
    "tradeoff_reasoning": "tradeoff_reasoning",
    "structured_communication": "structure",
    "clear_communication": "clarity",
}
_DIMENSIONS = ("correctness", "depth", "clarity", "structure", "tradeoff_reasoning", "risk_awareness")


def apply_company_modifiers(evaluation: Evaluation, emphasis: dict[str, float] | None) -> Evaluation:
    """Multiply evaluator dimensions by the company's emphasis and renormalize (§2.8).

    `emphasis` maps a dimension name to the weight of the company's observed skill
    on that dimension, e.g. {"risk_awareness": 0.30}. Multipliers are 1 + weight,
    divided by their mean so the overall scale is unchanged.
    """
    if not emphasis:
        return evaluation
    multipliers = {dim: 1.0 + emphasis.get(dim, 0.0) for dim in _DIMENSIONS}
    mean = sum(multipliers.values()) / len(multipliers)
    updates = {dim: clamp(getattr(evaluation, dim) * multipliers[dim] / mean, 0.0, 1.0) for dim in _DIMENSIONS}
    return evaluation.model_copy(update=updates)


# ----------------------------------------------------------------------------- §3.1 band


def classify_band(evaluation: Evaluation, core_misconception: bool = False,
                  params: EngineParams = DEFAULT_PARAMS) -> Band:
    p = params.scores
    if core_misconception or evaluation.correctness < p.partial_correctness:
        return Band.WEAK
    if evaluation.correctness >= p.strong_correctness and evaluation.depth >= p.strong_depth:
        return Band.STRONG
    return Band.PARTIAL


def classify_band_from_row(row: dict, params: EngineParams = DEFAULT_PARAMS) -> str | None:
    """Band of a stored metrics row. Uses the recorded band when present, else the score thresholds."""
    if row.get("band"):
        return row["band"]
    if row.get("correctness") is None or row.get("depth") is None:
        return None
    p = params.scores
    if row["correctness"] < p.partial_correctness:
        return Band.WEAK.value
    if row["correctness"] >= p.strong_correctness and row["depth"] >= p.strong_depth:
        return Band.STRONG.value
    return Band.PARTIAL.value


# ----------------------------------------------------------------------------- §2.9 evidence weight


def evidence_weight(mode: str, familiarity: str = "new", hint_level: int = 0, exposure_risk: str = "low",
                    revealed_before_submit: bool = False, params: EngineParams = DEFAULT_PARAMS) -> float:
    if revealed_before_submit:
        return 0.0
    e = params.evidence
    weight = (e.base[mode] * e.familiarity[familiarity]
              * e.assistance[int(clamp(hint_level, 0, 3))] * e.exposure[exposure_risk])
    return round(weight, 3)


# ----------------------------------------------------------------------------- §2.4 score update


def latency_norm(latency_ms: int | None, difficulty: int, params: EngineParams = DEFAULT_PARAMS) -> float:
    """1.0 within the expected time for this difficulty, falling to 0.0 at three times that."""
    if latency_ms is None:
        return 0.5
    p = params.scores
    expected = p.expected_answer_ms_base + p.expected_answer_ms_per_difficulty * difficulty
    ratio = latency_ms / expected
    if ratio <= 1.0:
        return 1.0
    return clamp(1.0 - (ratio - 1.0) / (p.latency_slow_ratio - 1.0), 0.0, 1.0)


def revision_norm(revision_count: int | None, params: EngineParams = DEFAULT_PARAMS) -> float:
    if revision_count is None:
        return 0.0
    return clamp(revision_count / params.scores.revision_cap, 0.0, 1.0)


@dataclass(frozen=True)
class ScoreUpdate:
    k_before: float
    k_after: float
    c_before: float
    c_after: float


def update_scores(*, k_old: float, c_old: float, evaluation: Evaluation, difficulty: int,
                  difficulty_ceiling: int, turns_on_skill: int, hint_level: int = 0,
                  latency_ms: int | None = None, revision_count: int | None = None,
                  weight: float = 1.0, params: EngineParams = DEFAULT_PARAMS) -> ScoreUpdate:
    """§2.4. `turns_on_skill` counts turns BEFORE this one. `weight` is the evidence weight (§2.9)."""
    p = params.scores
    difficulty_factor = p.difficulty_factor_base + p.difficulty_factor_span * (difficulty / max(difficulty_ceiling, 1))
    raw_knowledge = 100.0 * (p.knowledge_correctness_weight * evaluation.correctness
                             + p.knowledge_depth_weight * evaluation.depth)
    a_k = (p.a_k_first_turns if turns_on_skill < p.first_turns_count else p.a_k) * weight
    k_new = k_old + clamp(a_k * difficulty_factor, 0.0, 1.0) * (raw_knowledge - k_old)

    raw_confidence = 100.0 * (
        p.conf_clarity_weight * evaluation.clarity
        + p.conf_hedging_weight * (1.0 - evaluation.hedging_ratio)
        + p.conf_latency_weight * latency_norm(latency_ms, difficulty, params)
        + p.conf_revision_weight * (1.0 - revision_norm(revision_count, params))
    )
    hint_penalty = p.hint_penalty_per_level * hint_level
    a_c = clamp(p.a_c * weight, 0.0, 1.0)
    c_new = c_old + a_c * (raw_confidence - hint_penalty - c_old)

    return ScoreUpdate(k_before=round(k_old, 2), k_after=round(clamp(k_new, 0, 100), 2),
                       c_before=round(c_old, 2), c_after=round(clamp(c_new, 0, 100), 2))


# ----------------------------------------------------------------------------- §2.5 priors


@dataclass(frozen=True)
class Prior:
    k: float
    c: float
    source: str


def skill_prior(*, seniority: str, profile_k: float | None = None, profile_c: float | None = None,
                days_since_assessed: float | None = None, prerequisite_ks: list[float] | None = None,
                subject_k: float | None = None, calibration: str | None = None,
                params: EngineParams = DEFAULT_PARAMS) -> Prior:
    """Starting k and c for a skill before its first question, best evidence first."""
    p = params.scores
    c_adjust = {"overconfident": -p.calibration_prior_adjust,
                "underconfident": p.calibration_prior_adjust}.get(calibration or "", 0.0)

    if profile_k is not None:
        decay = (1.0 - p.prior_decay_per_30_days) ** ((days_since_assessed or 0.0) / 30.0)
        c_base = profile_c if profile_c is not None else p.prior_c_default
        return Prior(k=round(profile_k * decay, 2), c=round(clamp(c_base * decay + c_adjust, 0, 100), 2),
                     source="profile")
    if prerequisite_ks:
        k = sum(prerequisite_ks) / len(prerequisite_ks) + p.prior_prerequisite_offset
        return Prior(k=round(clamp(k, 0, 100), 2), c=clamp(p.prior_c_default + c_adjust, 0, 100),
                     source="prerequisites")
    if subject_k is not None:
        return Prior(k=round(clamp(subject_k + p.prior_subject_offset, 0, 100), 2),
                     c=clamp(p.prior_c_default + c_adjust, 0, 100), source="subject")
    return Prior(k=p.seniority_prior_k.get(seniority, p.seniority_prior_k["junior"]),
                 c=clamp(p.prior_c_default + c_adjust, 0, 100), source="seniority")


# ----------------------------------------------------------------------------- §2.6 levels


def level_from_difficulty(difficulty: int) -> int:
    """Difficulty 1-2 -> level 1, 3-4 -> 2, 5-6 -> 3, 7-8 -> 4, 9-10 -> 5."""
    return int(clamp((difficulty + 1) // 2, 1, 5))


def min_difficulty_for_level(level: int) -> int:
    return int(clamp(2 * level - 1, 1, 10))


def questioned_level(skill: SkillState, params: EngineParams = DEFAULT_PARAMS) -> tuple[int | None, float | None]:
    """(proficiency_level, level_score) for a questioned skill, or (None, None) with no turns."""
    if not skill.history:
        return None, None
    p = params.scores

    if skill.ceiling is not None:
        from_ceiling = level_from_difficulty(skill.ceiling)
    else:
        # ASSUMPTION: no STRONG answer yet. The candidate sits below the easiest difficulty asked.
        easiest = min(turn.difficulty for turn in skill.history)
        from_ceiling = max(1, level_from_difficulty(easiest) - 1)

    total_weight = sum(turn.evidence_weight for turn in skill.history)
    if total_weight > 0:
        from_rubric = sum(turn.rubric_level_estimate * turn.evidence_weight for turn in skill.history) / total_weight
    else:
        from_rubric = sum(turn.rubric_level_estimate for turn in skill.history) / len(skill.history)

    k = skill.k if skill.k is not None else 0.0
    level_score = (p.level_ceiling_weight * from_ceiling + p.level_rubric_weight * from_rubric
                   + p.level_k_weight * (k / 20.0))
    level = int(clamp(round_half_up(level_score), 1, 5))

    if skill.level3_hint_difficulty is not None:
        level = min(level, max(1, level_from_difficulty(skill.level3_hint_difficulty) - 1))
    if skill.core_misconception:
        level = min(level, p.core_misconception_level_cap)
    return level, round(level_score, 2)


def evidence_status(skill: SkillState, required_level: int) -> EvidenceStatus:
    """0 turns: not assessed. 1 turn: insufficient unless it was STRONG at or above the required difficulty."""
    scored = [turn for turn in skill.history if turn.evidence_weight > 0]
    if not scored:
        return EvidenceStatus.NOT_ASSESSED
    if len(scored) >= 2:
        return EvidenceStatus.ASSESSED
    only = scored[0]
    if only.band == Band.STRONG and only.difficulty >= min_difficulty_for_level(required_level):
        return EvidenceStatus.ASSESSED
    return EvidenceStatus.INSUFFICIENT


def record_turn(skill: SkillState, *, difficulty: int, band: Band, evaluation: Evaluation, hint_level: int,
                weight: float, core_misconception: bool, archetype: Archetype = Archetype.CONCEPTUAL,
                params: EngineParams = DEFAULT_PARAMS) -> None:
    """Append the turn to the skill's history and refresh ceiling and provisional level."""
    skill.history.append(TurnRecord(difficulty=difficulty, band=band, hint_level=hint_level,
                                    rubric_level_estimate=evaluation.rubric_level_estimate,
                                    evidence_weight=weight, core_misconception=core_misconception,
                                    archetype=archetype))
    skill.turns += 1
    if hint_level > 0:
        skill.hints_used += 1
    if hint_level >= 3 and skill.level3_hint_difficulty is None:
        skill.level3_hint_difficulty = difficulty
    if core_misconception:
        skill.core_misconception = True
    if band == Band.STRONG and hint_level < 3 and weight > 0:
        skill.ceiling = max(skill.ceiling or 0, difficulty)
    skill.provisional_level, _ = questioned_level(skill, params)


# ----------------------------------------------------------------------------- §2.7 observed skills

RELEVANT_ARCHETYPES = {
    "risk_awareness": {Archetype.DESIGN, Archetype.DEBUGGING},
    "tradeoff_reasoning": {Archetype.DESIGN},
    "structured_communication": {Archetype.DESIGN, Archetype.BEHAVIORAL, Archetype.CONCEPTUAL},
}


def observed_level(mean: float, params: EngineParams = DEFAULT_PARAMS) -> int:
    t1, t2, t3, t4 = params.scores.observed_level_thresholds
    if mean < t1:
        return 1
    if mean < t2:
        return 2
    if mean < t3:
        return 3
    if mean < t4:
        return 4
    return 5


def update_observed(state: ObservedState, evaluation: Evaluation, archetype: Archetype,
                    params: EngineParams = DEFAULT_PARAMS) -> None:
    dimension = DIMENSION_FOR_OBSERVED_SKILL.get(state.key)
    if dimension is None:
        return
    relevant = archetype in RELEVANT_ARCHETYPES.get(state.key, set())
    relevance = 1.0 if relevant else params.scores.observed_relevance_default
    state.weighted_sum += getattr(evaluation, dimension) * relevance
    state.relevance_sum += relevance
    state.n += 1
    state.n_relevant += int(relevant)
    state.provisional_level = observed_level(state.weighted_sum / state.relevance_sum, params)


def observed_status(state: ObservedState, params: EngineParams = DEFAULT_PARAMS) -> EvidenceStatus:
    if state.n == 0:
        return EvidenceStatus.NOT_ASSESSED
    if state.n_relevant >= params.scores.observed_min_relevant_turns:
        return EvidenceStatus.ASSESSED
    return EvidenceStatus.INSUFFICIENT


# ----------------------------------------------------------------------------- §2.10 calibration


def calibration(pairs: list[tuple[int, float]], params: EngineParams = DEFAULT_PARAMS) -> tuple[float | None, str | None]:
    """pairs = [(self_confidence 1-5, correctness 0-1)]. Returns (error, label)."""
    if not pairs:
        return None, None
    error = sum(conf / 5.0 - correct for conf, correct in pairs) / len(pairs)
    band = params.scores.calibration_band
    label = "overconfident" if error > band else "underconfident" if error < -band else "well_calibrated"
    return round(error, 3), label


# ----------------------------------------------------------------------------- momentum

BAND_VALUE = {Band.STRONG: 1.0, Band.PARTIAL: 0.0, Band.WEAK: -1.0}


def momentum(bands: list[Band], window: int) -> float:
    recent = bands[-window:]
    if not recent:
        return 0.0
    return round(sum(BAND_VALUE[b] for b in recent) / len(recent), 2)
