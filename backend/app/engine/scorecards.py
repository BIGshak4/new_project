"""Skill-set scorecards and the long-term profile (Data_Models §7.2, §7.3, §7.4)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.engine.params import DEFAULT_PARAMS, EngineParams
from app.engine.scores import round_half_up
from app.schemas.engine import EvidenceStatus, Importance


@dataclass(frozen=True)
class AssessedSkill:
    """One row of user_skill_assessment, reduced to what the fit formula needs."""

    key: str
    weight: float
    importance: Importance
    required_level: int
    status: EvidenceStatus
    proficiency_level: int | None
    subject: str | None = None

    @property
    def level_gap(self) -> int | None:
        return None if self.proficiency_level is None else self.proficiency_level - self.required_level


@dataclass
class Scorecard:
    fit_score: float | None
    skills_total: int
    skills_assessed: int
    skills_meeting_requirement: int
    core_gaps: list[str] = field(default_factory=list)
    top_strengths: list[str] = field(default_factory=list)
    domain_breakdown: dict[str, float] = field(default_factory=dict)
    partial_evaluation: bool = False
    cap_applied: float | None = None


def _weighted_fit(skills: list[AssessedSkill]) -> float | None:
    total = sum(s.weight for s in skills)
    if total <= 0:
        return None
    return 100.0 * sum(s.weight * min(s.proficiency_level / s.required_level, 1.0) for s in skills) / total


def build_scorecard(skills: list[AssessedSkill], params: EngineParams = DEFAULT_PARAMS) -> Scorecard:
    """§7.2: weighted fit over assessed skills, then the core-gap cap."""
    p = params.scorecards
    assessed = [s for s in skills if s.status == EvidenceStatus.ASSESSED and s.proficiency_level is not None]
    fit = _weighted_fit(assessed)

    core_gaps = [s for s in assessed if s.importance == Importance.CORE and s.level_gap is not None and s.level_gap < 0]
    cap = None
    if fit is not None and core_gaps:
        worst = min(s.level_gap for s in core_gaps)
        cap = p.core_gap_two_levels_cap if worst <= -2 else p.core_gap_one_level_cap
        fit = min(fit, cap)

    strengths = sorted((s for s in assessed if (s.level_gap or 0) > 0), key=lambda s: (-s.level_gap, -s.weight))[:3]
    breakdown: dict[str, float] = {}
    for subject in dict.fromkeys(s.subject for s in assessed if s.subject):
        value = _weighted_fit([s for s in assessed if s.subject == subject])
        if value is not None:
            breakdown[subject] = round(value, 2)

    return Scorecard(
        fit_score=None if fit is None else round(fit, 2),
        skills_total=len(skills), skills_assessed=len(assessed),
        skills_meeting_requirement=sum(1 for s in assessed if (s.level_gap or 0) >= 0),
        core_gaps=[s.key for s in sorted(core_gaps, key=lambda s: (s.level_gap, -s.weight))],
        top_strengths=[s.key for s in strengths], domain_breakdown=breakdown,
        partial_evaluation=bool(skills) and len(assessed) / len(skills) < p.partial_evaluation_coverage,
        cap_applied=cap if cap is not None and fit == cap else None,
    )


# ----------------------------------------------------------------------------- §7.3 profile roll-up


@dataclass(frozen=True)
class PastAssessment:
    proficiency_level: int
    turns_count: int


@dataclass(frozen=True)
class ProfileRollup:
    proficiency_level: int
    level_score: float
    trend: str
    assessments_count: int
    evidence_turns_total: int


def roll_up_profile(assessments_newest_first: list[PastAssessment],
                    params: EngineParams = DEFAULT_PARAMS) -> ProfileRollup | None:
    """w_i = turns_i x 0.7^i, newest first. More evidence and more recent count more."""
    if not assessments_newest_first:
        return None
    p = params.scorecards
    weights = [max(a.turns_count, 1) * p.rollup_recency_decay ** i for i, a in enumerate(assessments_newest_first)]
    score = sum(w * a.proficiency_level for w, a in zip(weights, assessments_newest_first, strict=True)) / sum(weights)

    levels = [a.proficiency_level for a in assessments_newest_first]
    if len(levels) == 1:
        trend = "new"
    else:
        previous = levels[1:3]
        delta = levels[0] - sum(previous) / len(previous)
        trend = ("improving" if delta >= p.trend_threshold
                 else "declining" if delta <= -p.trend_threshold else "stable")
    return ProfileRollup(proficiency_level=max(1, min(5, round_half_up(score))), level_score=round(score, 2),
                         trend=trend, assessments_count=len(levels),
                         evidence_turns_total=sum(a.turns_count for a in assessments_newest_first))


# ----------------------------------------------------------------------------- §7.4 target fit


@dataclass
class TargetFit:
    fit_score: float | None
    known_coverage: float
    unknown_skills: list[str]
    core_gaps: list[str]


def target_fit(merged_plan: list, profile_levels: dict[str, int],
               params: EngineParams = DEFAULT_PARAMS) -> TargetFit:
    """Score the long-term profile against any role + company, without a new interview.

    `merged_plan` is the §6.3 merge WITHOUT user focus. Skills never assessed count
    as unknown, not zero.
    """
    known, unknown = [], []
    for skill in merged_plan:
        if skill.key in profile_levels:
            known.append(AssessedSkill(key=skill.key, weight=skill.combined_weight, importance=skill.importance,
                                       required_level=skill.required_level, status=EvidenceStatus.ASSESSED,
                                       proficiency_level=profile_levels[skill.key], subject=skill.subject))
        else:
            unknown.append(skill.key)
    card = build_scorecard(known, params)
    total_weight = sum(s.combined_weight for s in merged_plan) or 1.0
    return TargetFit(fit_score=card.fit_score,
                     known_coverage=round(sum(s.weight for s in known) / total_weight, 3),
                     unknown_skills=unknown, core_gaps=card.core_gaps)
