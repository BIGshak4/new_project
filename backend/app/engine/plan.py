"""Skill-set merge: role set + company set + user focus -> session skill plan.

Implements Data_Models §6.3 step by step. Run once at session start; the result
is frozen for the session and sits in the cached prompt prefix.
"""

from __future__ import annotations

from app.engine.params import DEFAULT_PARAMS, EngineParams
from app.engine.scores import clamp, round_half_up
from app.schemas.engine import (
    IMPORTANCE_RANK,
    AssessmentMode,
    CatalogSkill,
    CompanySkillRow,
    Importance,
    PlanSkill,
    RoleSkillRow,
    SkillSource,
)

USER_FOCUS_BONUS = 0.10
COMPANY_ONLY_DEFAULT_LEVEL = 3
CORE_MIN_TURNS = 2


def company_rows_for_role(rows: list[CompanySkillRow], *, role_slug: str, role_family: str) -> list[CompanySkillRow]:
    """Company rows that apply: all roles, this family, or this specific role."""
    return [row for row in rows
            if row.scope == "all_roles"
            or (row.scope == "family" and row.scope_family == role_family)
            or (row.scope == "role" and row.scope_role == role_slug)]


def merge_skill_sets(*, role_rows: list[RoleSkillRow], company_rows: list[CompanySkillRow],
                     focus_skill_keys: list[str], company_weight_share: float, seniority: str,
                     planned_duration_min: float, catalog: dict[str, CatalogSkill],
                     params: EngineParams = DEFAULT_PARAMS) -> list[PlanSkill]:
    share = company_weight_share if company_rows else 0.0

    # 1. normalize each side
    role_total = sum(row.weight for row in role_rows) or 1.0
    company_total = sum(row.weight for row in company_rows) or 1.0
    role_by_key = {row.skill: row for row in role_rows}
    company_by_key = {row.skill: row for row in company_rows}

    # 2. merge every skill in R ∪ C
    drafts: dict[str, dict] = {}
    for key in list(role_by_key) + [k for k in company_by_key if k not in role_by_key]:
        role, company = role_by_key.get(key), company_by_key.get(key)
        role_w = role.weight / role_total if role else 0.0
        company_w = company.weight / company_total if company else 0.0
        skill = catalog[key]

        if role and company:
            source = SkillSource.ROLE_AND_COMPANY
            required = _role_level(role, seniority) + company.required_level_offset
        elif role:
            source = SkillSource.ROLE
            required = _role_level(role, seniority)
        else:
            source = SkillSource.COMPANY
            required = company.required_level_min or COMPANY_ONLY_DEFAULT_LEVEL

        importances = [r.importance for r in (role, company) if r]
        mode = ((company.assessment_mode if company else None) or (role.assessment_mode if role else None)
                or skill.default_assessment_mode or AssessmentMode.QUESTIONED)
        notes = " ".join(n for n in ((role.evaluation_notes if role else None),
                                      (company.examination_notes if company else None)) if n) or None
        drafts[key] = {
            "source": source, "role_weight": role_w, "company_weight": company_w,
            "combined": (1.0 - share) * role_w + share * company_w,
            "importance": max(importances, key=lambda i: IMPORTANCE_RANK[i]),
            "required_level": int(clamp(required, 1, 5)), "mode": mode, "notes": notes, "focus": False,
        }

    # 3. user focus adds 0.10, and adds the skill if it is not in the plan
    for key in focus_skill_keys:
        if key not in catalog:
            continue
        if key in drafts:
            drafts[key]["combined"] += USER_FOCUS_BONUS
            drafts[key]["focus"] = True
        else:
            skill = catalog[key]
            drafts[key] = {
                "source": SkillSource.USER_FOCUS, "role_weight": 0.0, "company_weight": 0.0,
                "combined": USER_FOCUS_BONUS, "importance": Importance.IMPORTANT,
                "required_level": COMPANY_ONLY_DEFAULT_LEVEL,
                "mode": skill.default_assessment_mode or AssessmentMode.QUESTIONED, "notes": None, "focus": True,
            }

    # 4. renormalize to 1.0
    total = sum(d["combined"] for d in drafts.values()) or 1.0
    for draft in drafts.values():
        draft["combined"] /= total

    # 5. allocate question turns (questioned skills only)
    expected_turns = planned_duration_min / params.router.minutes_per_turn
    plan: list[PlanSkill] = []
    for key, draft in drafts.items():
        skill = catalog[key]
        turns = 0
        if draft["mode"] == AssessmentMode.QUESTIONED:
            turns = round_half_up(draft["combined"] * expected_turns)
            if draft["importance"] == Importance.CORE:
                turns = max(turns, CORE_MIN_TURNS)
        plan.append(PlanSkill(
            key=key, subject=skill.subject or key, source=draft["source"],
            role_weight=round(draft["role_weight"], 4), company_weight=round(draft["company_weight"], 4),
            combined_weight=round(draft["combined"], 4), importance=draft["importance"],
            required_level=draft["required_level"], assessment_mode=draft["mode"], planned_turns=turns,
            min_difficulty=skill.min_difficulty, max_difficulty=skill.max_difficulty,
            prerequisites=[p for p in skill.prerequisites if p in drafts],
            in_user_focus=draft["focus"], examination_notes=draft["notes"],
        ))

    # 6. priority: core first, then weight, then prerequisites before dependents
    plan.sort(key=lambda s: (s.importance != Importance.CORE, -s.combined_weight, s.key))
    plan = _prerequisites_first(plan)
    for rank, skill in enumerate(plan, start=1):
        skill.priority_rank = rank
    return plan


def _role_level(row: RoleSkillRow, seniority: str) -> int:
    if seniority in row.required_level:
        return row.required_level[seniority]
    # a role that does not list this seniority falls back to the nearest one it does list
    order = ["student", "junior", "mid", "senior", "staff", "principal"]
    index = order.index(seniority) if seniority in order else 1
    for distance in range(1, len(order)):
        for candidate in (index - distance, index + distance):
            if 0 <= candidate < len(order) and order[candidate] in row.required_level:
                return row.required_level[order[candidate]]
    return COMPANY_ONLY_DEFAULT_LEVEL


def _prerequisites_first(plan: list[PlanSkill]) -> list[PlanSkill]:
    """Stable reorder so a prerequisite never ranks after the skill that needs it."""
    ordered: list[PlanSkill] = []
    placed: set[str] = set()
    by_key = {skill.key: skill for skill in plan}

    def place(skill: PlanSkill, trail: tuple[str, ...] = ()) -> None:
        if skill.key in placed or skill.key in trail:
            return
        for prerequisite in skill.prerequisites:
            if prerequisite in by_key:
                place(by_key[prerequisite], trail + (skill.key,))
        placed.add(skill.key)
        ordered.append(skill)

    for skill in plan:
        place(skill)
    return ordered
