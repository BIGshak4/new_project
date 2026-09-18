"""Post-session report (AI_Engine_Spec §7).

Everything numeric is computed here, by code, from the session state and the
metrics rows. The model only writes the narrative from that structured data, so a
level or a score in the report can always be traced to evidence.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from app.engine import i18n, scores, tips
from app.engine.params import DEFAULT_PARAMS, EngineParams
from app.engine.providers import LLMError, LLMRequest, Provider
from app.engine.scorecards import AssessedSkill, Scorecard, build_scorecard
from app.schemas.bank import Tip
from app.schemas.engine import (
    AssessmentMode,
    EvidenceStatus,
    Importance,
    PlanSkill,
    SessionState,
    SkillSource,
)


@dataclass
class SkillAssessment:
    key: str
    subject: str
    source: str
    assessment_mode: str
    status: str
    turns_count: int
    knowledge_score: float | None
    confidence_score: float | None
    demonstrated_ceiling: int | None
    proficiency_level: int | None
    required_level: int
    hints_used: int
    importance: str
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)

    @property
    def level_gap(self) -> int | None:
        return None if self.proficiency_level is None else self.proficiency_level - self.required_level


@dataclass
class ReportData:
    assessments: list[SkillAssessment]
    subjects: list[dict]
    scorecards: dict[str, Scorecard]
    timeline: list[dict]
    recommended_next_skills: list[str]
    cover_next_time: list[str]
    top_tips: list[str]
    generated_turns: list[int]


def assess_skills(state: SessionState, plan: list[PlanSkill], notes: dict[str, dict] | None = None,
                  params: EngineParams = DEFAULT_PARAMS) -> list[SkillAssessment]:
    """One assessment per planned skill. `notes` maps skill key to {"hit": [...], "missed": [...]}."""
    notes = notes or {}
    assessments = []
    for skill in plan:
        note = notes.get(skill.key, {})
        if skill.assessment_mode == AssessmentMode.OBSERVED:
            observed = state.observed_state[skill.key]
            status = scores.observed_status(observed, params)
            level = observed.provisional_level if status != EvidenceStatus.NOT_ASSESSED else None
            assessments.append(SkillAssessment(
                key=skill.key, subject=skill.subject, source=skill.source.value, assessment_mode="observed",
                status=status.value, turns_count=observed.n, knowledge_score=None, confidence_score=None,
                demonstrated_ceiling=None, proficiency_level=level, required_level=skill.required_level,
                hints_used=0, importance=skill.importance.value))
            continue
        skill_state = state.skill_state[skill.key]
        status = scores.evidence_status(skill_state, skill.required_level)
        level, _ = scores.questioned_level(skill_state, params)
        assessments.append(SkillAssessment(
            key=skill.key, subject=skill.subject, source=skill.source.value, assessment_mode="questioned",
            status=status.value, turns_count=skill_state.turns,
            knowledge_score=skill_state.k if skill_state.turns else None,
            confidence_score=skill_state.c if skill_state.turns else None,
            demonstrated_ceiling=skill_state.ceiling,
            proficiency_level=level if status != EvidenceStatus.NOT_ASSESSED else None,
            required_level=skill.required_level, hints_used=skill_state.hints_used, importance=skill.importance.value,
            strengths=list(dict.fromkeys(note.get("hit", [])))[:4], gaps=list(dict.fromkeys(note.get("missed", [])))[:4]))
    return assessments


def _scorecard(assessments: list[SkillAssessment], plan: list[PlanSkill], scope: str,
               params: EngineParams) -> Scorecard | None:
    by_key = {s.key: s for s in plan}
    sources = {"role": (SkillSource.ROLE, SkillSource.ROLE_AND_COMPANY),
               "company": (SkillSource.COMPANY, SkillSource.ROLE_AND_COMPANY)}
    rows = []
    for assessment in assessments:
        skill = by_key[assessment.key]
        if scope in sources and skill.source not in sources[scope]:
            continue
        weight = {"role": skill.role_weight, "company": skill.company_weight}.get(scope, skill.combined_weight)
        rows.append(AssessedSkill(key=skill.key, weight=weight, importance=skill.importance,
                                  required_level=skill.required_level, status=EvidenceStatus(assessment.status),
                                  proficiency_level=assessment.proficiency_level, subject=skill.subject))
    return build_scorecard(rows, params) if rows else None


def build_report(state: SessionState, plan: list[PlanSkill], metrics_rows: list[dict], *,
                 notes: dict[str, dict] | None = None, delivered_tip_keys: list[str] | None = None,
                 tips_library: list[Tip] | None = None, generated_turns: list[int] | None = None,
                 params: EngineParams = DEFAULT_PARAMS) -> ReportData:
    assessments = assess_skills(state, plan, notes, params)
    by_key = {s.key: s for s in plan}

    scorecards = {scope: card for scope in ("role", "company", "session_overall")
                  if (card := _scorecard(assessments, plan, scope, params)) is not None}

    subjects = []
    for subject in state.subject_state.values():
        if subject.skills_planned == 0:
            continue
        reasons = sorted({code for row in metrics_rows if row.get("subject_key") == subject.key
                          for code in str(row.get("decision_reason_code", "")).split(",")
                          if code.startswith("rebalance_") or code == "subject_closed_early"})
        subjects.append({"key": subject.key, "status": subject.status.value, "level": subject.level,
                         "required_level": subject.required_level, "turns_used": subject.turns_used,
                         "turns_planned": subject.turns_planned_original, "rebalance_reasons": reasons})

    timeline = [{"turn": row.get("turn_index"), "subject": row.get("subject_key"), "skill": row.get("skill_key"),
                 "difficulty": row.get("difficulty_asked"), "action": row.get("decision_action"),
                 "band": scores.classify_band_from_row(row)} for row in metrics_rows]

    # next focus: combined_weight x gap, core first; insufficient evidence is "cover next time"
    gaps = [a for a in assessments if a.status == EvidenceStatus.ASSESSED.value and (a.level_gap or 0) < 0]
    gaps.sort(key=lambda a: (a.importance != Importance.CORE.value,
                             -by_key[a.key].combined_weight * abs(a.level_gap)))
    recommended = [a.key for a in gaps]
    cover_next = [a.key for a in assessments if a.status != EvidenceStatus.ASSESSED.value
                  and a.assessment_mode == "questioned"]

    top = list(dict.fromkeys(delivered_tip_keys or []))
    for tip in tips.tips_for_gaps(tips_library or [], recommended):
        if tip.key not in top:
            top.append(tip.key)
    return ReportData(assessments=assessments, subjects=subjects, scorecards=scorecards, timeline=timeline,
                      recommended_next_skills=recommended, cover_next_time=cover_next, top_tips=top[:5],
                      generated_turns=generated_turns or [])


def fallback_narrative(data: ReportData, labels: dict[str, str], language: str) -> str:
    """A plain report from the data alone, used when the model call fails."""
    heading = {"en": ("Summary", "Subjects", "Practice next", "Not enough evidence yet"),
               "he": ("סיכום", "נושאים", "מה לתרגל הלאה", "עדיין אין מספיק מידע")}.get(language) \
        or ("Summary", "Subjects", "Practice next", "Not enough evidence yet")
    lines = [f"## {heading[0]}"]
    overall = data.scorecards.get("session_overall")
    if overall and overall.fit_score is not None:
        lines.append(f"- Fit: {overall.fit_score:.0f}% ({overall.skills_assessed}/{overall.skills_total})")
    lines.append(f"\n## {heading[1]}")
    for subject in data.subjects:
        level = "-" if subject["level"] is None else f"{subject['level']:.1f}"
        lines.append(f"- {labels.get(subject['key'], subject['key'])}: {level} / {subject['required_level']:.1f} "
                     f"({subject['status']}, {subject['turns_used']}/{subject['turns_planned']})")
    if data.recommended_next_skills:
        lines.append(f"\n## {heading[2]}")
        lines += [f"- {labels.get(k, k)}" for k in data.recommended_next_skills[:5]]
    if data.cover_next_time:
        lines.append(f"\n## {heading[3]}")
        lines += [f"- {labels.get(k, k)}" for k in data.cover_next_time[:8]]
    return "\n".join(lines)


async def narrative(provider: Provider | None, data: ReportData, *, language: str, labels: dict[str, str],
                    tone: str | None = None, glossary: list[dict] | None = None) -> tuple[str, str]:
    """Returns (markdown, source). The structured data is the single source of truth."""
    plain = fallback_narrative(data, labels, language)
    if provider is None:
        return plain, "fallback"
    payload = {
        "practice_language": i18n.LANGUAGE_NAMES.get(language, "English"), "tone": tone,
        "skill_labels": labels,
        "assessments": [{**asdict(a), "level_gap": a.level_gap} for a in data.assessments],
        "subjects": data.subjects,
        "scorecards": {k: asdict(v) for k, v in data.scorecards.items()},
        "timeline": data.timeline, "recommended_next_skills": data.recommended_next_skills,
        "cover_next_time": data.cover_next_time, "tips": data.top_tips, "generated_turns": data.generated_turns,
    }
    request = LLMRequest(role="report", system=[i18n.stable_system_block("report", language, glossary)],
                         user=json.dumps(payload, ensure_ascii=False, indent=1),
                         prompt_version=i18n.prompt_version("report"))
    try:
        response = await provider.complete(request)
    except LLMError:
        return plain, "fallback"
    return (response.text.strip() or plain), "generated"
