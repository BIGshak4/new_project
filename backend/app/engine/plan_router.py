"""The Plan Router: adaptation across days (AI_Engine_Spec §4.11).

The Subject Router works inside one session. This chooses the next activity and the
weekly plan from everything the user has done. Pure functions; the caller supplies
the profile and persists the result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from app.engine.params import DEFAULT_PARAMS, EngineParams
from app.schemas.engine import AssessmentMode, EvidenceStatus, Importance, PlanSkill


@dataclass
class ProfileSkill:
    """What the Plan Router needs to know about one skill in the user's profile."""

    key: str
    level: int | None = None
    status: EvidenceStatus = EvidenceStatus.NOT_ASSESSED
    retention_due_at: date | None = None
    retention_checks_passed: int = 0
    loyalty: int | None = None                 # 1..10 evidence freshness; None when never assessed
    days_since_assessed: int | None = None

    @property
    def stale(self) -> bool:
        """The level exists but its evidence is old enough to count as provisional (scores.needs_refresh)."""
        from app.engine.scores import needs_refresh
        return self.level is not None and needs_refresh(self.loyalty)


@dataclass
class RecentActivity:
    mode: str
    band: str | None = None            # STRONG | PARTIAL | WEAK for the activity as a whole


@dataclass
class Activity:
    mode: str                          # quick | deep | simulation | diagnostic | retention_check
    skills: list[str]
    estimated_minutes: int
    value: float = 0.0
    reason_code: str = ""
    reason_facts: dict = field(default_factory=dict)
    hard: bool = False


@dataclass
class PlannedItem:
    day_index: int
    activity: Activity


# ----------------------------------------------------------------------------- retention


def schedule_retention(*, level_before: int | None, level_after: int | None, today: date,
                       checks_passed: int = 0, params: EngineParams = DEFAULT_PARAMS) -> date | None:
    """A level that rose gets a check 3 to 5 days later on an unfamiliar question.

    A first assessment is not a rise: there was no earlier level to retain.
    """
    if level_before is None or level_after is None or level_after <= level_before:
        return None
    low, high = params.plan_router.retention_first_days if checks_passed == 0 else params.plan_router.retention_next_days
    return today + timedelta(days=(low + high) // 2)


def after_retention_check(*, passed: bool, today: date, checks_passed: int,
                          params: EngineParams = DEFAULT_PARAMS) -> tuple[date | None, int]:
    """Held: confirm and check again in 10 to 14 days. Failed: the skill returns to focus, no new check yet."""
    if not passed:
        return None, 0
    low, high = params.plan_router.retention_next_days
    return today + timedelta(days=(low + high) // 2), checks_passed + 1


# ----------------------------------------------------------------------------- scoring


def _gap(skill: PlanSkill, profile: dict[str, ProfileSkill]) -> int:
    entry = profile.get(skill.key)
    if entry is None or entry.level is None or entry.status == EvidenceStatus.NOT_ASSESSED:
        return 0
    return max(0, skill.required_level - entry.level)


def _unassessed(skill: PlanSkill, profile: dict[str, ProfileSkill]) -> bool:
    entry = profile.get(skill.key)
    return entry is None or entry.status == EvidenceStatus.NOT_ASSESSED


def coverage(plan: list[PlanSkill], profile: dict[str, ProfileSkill]) -> float:
    questioned = [s for s in plan if s.assessment_mode == AssessmentMode.QUESTIONED]
    if not questioned:
        return 1.0
    return sum(1 for s in questioned if not _unassessed(s, profile)) / len(questioned)


def activity_value(activity: Activity, *, plan: list[PlanSkill], profile: dict[str, ProfileSkill], today: date,
                   recent: list[RecentActivity], minutes_available_today: int,
                   params: EngineParams = DEFAULT_PARAMS) -> float:
    p = params.plan_router
    by_key = {s.key: s for s in plan}
    skills = [by_key[k] for k in activity.skills if k in by_key]
    w_unassessed = p.w_unassessed_late if coverage(plan, profile) >= p.coverage_switch else p.w_unassessed_early
    due = [s for s in skills if (entry := profile.get(s.key))
           and ((entry.retention_due_at and entry.retention_due_at <= today) or entry.stale)]
    core_below = any(s.importance == Importance.CORE and _gap(s, profile) > 0 for s in skills)
    last_two = recent[-2:]
    variety = bool(last_two) and all(a.mode != activity.mode for a in last_two)
    fatigued = len(last_two) == 2 and all(a.band == "WEAK" for a in last_two) and activity.hard
    return round(
        p.w_gap * sum(s.combined_weight * _gap(s, profile) for s in skills)
        + w_unassessed * sum(s.combined_weight for s in skills if _unassessed(s, profile))
        + p.w_retention * len(due)
        + p.w_core * core_below
        + p.w_variety * variety
        - p.w_fatigue * fatigued
        - p.w_time * max(0, activity.estimated_minutes - minutes_available_today) / 10, 4)


# ----------------------------------------------------------------------------- candidates


def candidate_activities(*, plan: list[PlanSkill], profile: dict[str, ProfileSkill], today: date,
                         bank_coverage: dict[str, dict[str, int]], week_index: int = 0,
                         params: EngineParams = DEFAULT_PARAMS) -> list[Activity]:
    minutes = params.plan_router.estimated_minutes
    questioned = [s for s in plan if s.assessment_mode == AssessmentMode.QUESTIONED]
    activities: list[Activity] = []

    for skill in questioned:
        entry = profile.get(skill.key)
        gap, unassessed = _gap(skill, profile), _unassessed(skill, profile)
        if entry and entry.retention_due_at and entry.retention_due_at <= today:
            activities.append(Activity("retention_check", [skill.key], minutes["retention_check"],
                                       reason_code="retention_due",
                                       reason_facts={"skill": skill.key, "level": entry.level}))
        elif entry and entry.stale:
            # the level is old news (loyalty in the provisional band): re-check it before building on it
            activities.append(Activity("retention_check", [skill.key], minutes["retention_check"],
                                       reason_code="stale",
                                       reason_facts={"skill": skill.key, "level": entry.level, "days": entry.days_since_assessed}))
        available = bank_coverage.get(skill.key, {})
        for mode in ("quick", "deep"):
            if not available.get(mode):
                continue
            if gap > 0:
                code = "core_gap" if skill.importance == Importance.CORE else "gap"
            elif unassessed:
                code = "unassessed"
            else:
                code = "keep_sharp"
            activities.append(Activity(mode, [skill.key], minutes[mode], reason_code=code, hard=gap > 0 and mode == "deep",
                                       reason_facts={"skill": skill.key, "level": entry.level if entry else None,
                                                     "required": skill.required_level}))

    if week_index >= 1 or coverage(plan, profile) >= params.plan_router.coverage_switch:
        top = sorted(questioned, key=lambda s: -s.combined_weight)[:6]
        activities.append(Activity("simulation", [s.key for s in top], minutes["simulation"], reason_code="simulation",
                                   hard=True, reason_facts={}))
    return activities


# ----------------------------------------------------------------------------- next activity and week


def next_activity(*, plan: list[PlanSkill], profile: dict[str, ProfileSkill], today: date,
                  recent: list[RecentActivity], minutes_available_today: int,
                  bank_coverage: dict[str, dict[str, int]], week_index: int = 0,
                  days_to_interview: int | None = None, diagnostic_done: bool = True,
                  params: EngineParams = DEFAULT_PARAMS) -> Activity | None:
    """The single recommended thing to do now."""
    if not diagnostic_done:
        return Activity("diagnostic", diagnostic_skills(plan, params=params),
                        params.plan_router.estimated_minutes["diagnostic"], value=99.0, reason_code="diagnostic")
    candidates = candidate_activities(plan=plan, profile=profile, today=today, bank_coverage=bank_coverage,
                                      week_index=week_index, params=params)
    if days_to_interview is not None and days_to_interview <= params.plan_router.final_days_reserved:
        reserved = [a for a in candidates if a.mode in ("simulation", "retention_check")]
        candidates = reserved or candidates
    for activity in candidates:
        activity.value = activity_value(activity, plan=plan, profile=profile, today=today, recent=recent,
                                        minutes_available_today=minutes_available_today, params=params)
    if not candidates:
        return None
    return max(candidates, key=lambda a: (a.value, -a.estimated_minutes, a.skills[0] if a.skills else ""))


def weekly_plan(*, plan: list[PlanSkill], profile: dict[str, ProfileSkill], week_start: date,
                minutes_per_day: int, bank_coverage: dict[str, dict[str, int]], week_index: int = 0,
                days_to_interview: int | None = None, recent: list[RecentActivity] | None = None,
                params: EngineParams = DEFAULT_PARAMS) -> list[PlannedItem]:
    """Top-value activities laid over seven days within the user's minutes, alternating modes."""
    history = list(recent or [])
    items: list[PlannedItem] = []
    used: set[tuple[str, tuple[str, ...]]] = set()
    has_deep = has_simulation = False

    for day in range(7):
        today = week_start + timedelta(days=day)
        remaining_days = None if days_to_interview is None else days_to_interview - day
        if remaining_days is not None and remaining_days < 0:
            break
        budget = minutes_per_day
        while budget > 0:
            candidates = candidate_activities(plan=plan, profile=profile, today=today, bank_coverage=bank_coverage,
                                              week_index=week_index, params=params)
            if remaining_days is not None and remaining_days <= params.plan_router.final_days_reserved:
                reserved = [a for a in candidates if a.mode in ("simulation", "retention_check")]
                candidates = reserved or candidates
            candidates = [a for a in candidates if (a.mode, tuple(a.skills)) not in used
                          and a.estimated_minutes <= max(budget, 5)]
            if not candidates:
                break
            for activity in candidates:
                activity.value = activity_value(activity, plan=plan, profile=profile, today=today, recent=history,
                                                minutes_available_today=budget, params=params)
            best = max(candidates, key=lambda a: (a.value, -a.estimated_minutes, a.skills[0] if a.skills else ""))
            if best.value <= 0 and items:
                break
            items.append(PlannedItem(day, best))
            used.add((best.mode, tuple(best.skills)))
            history.append(RecentActivity(best.mode))
            has_deep |= best.mode == "deep"
            has_simulation |= best.mode == "simulation"
            budget -= best.estimated_minutes

    # at least one deep practice per week; one simulation from week two when time allows
    minutes = params.plan_router.estimated_minutes
    if not has_deep:
        deep = [a for a in candidate_activities(plan=plan, profile=profile, today=week_start,
                                                bank_coverage=bank_coverage, week_index=week_index, params=params)
                if a.mode == "deep"]
        if deep:
            items.append(PlannedItem(min(6, len({i.day_index for i in items})), deep[0]))
    if not has_simulation and week_index >= 1 and minutes_per_day * 7 >= minutes["simulation"]:
        top = sorted((s for s in plan if s.assessment_mode == AssessmentMode.QUESTIONED),
                     key=lambda s: -s.combined_weight)[:6]
        items.append(PlannedItem(6, Activity("simulation", [s.key for s in top], minutes["simulation"],
                                             reason_code="simulation", hard=True)))
    return sorted(items, key=lambda i: i.day_index)


# ----------------------------------------------------------------------------- diagnostic and reasons


def diagnostic_skills(plan: list[PlanSkill], n_items: int | None = None,
                      params: EngineParams = DEFAULT_PARAMS) -> list[str]:
    """8 to 12 quick items spread across the role's subjects, heaviest skills first within each subject."""
    low, high = params.plan_router.diagnostic_items
    questioned = [s for s in plan if s.assessment_mode == AssessmentMode.QUESTIONED]
    target = n_items or max(low, min(high, len(questioned)))
    by_subject: dict[str, list[PlanSkill]] = {}
    for skill in sorted(questioned, key=lambda s: -s.combined_weight):
        by_subject.setdefault(skill.subject, []).append(skill)
    picks: list[str] = []
    while len(picks) < target and any(by_subject.values()):
        for subject in sorted(by_subject, key=lambda k: -sum(s.combined_weight for s in by_subject[k])):
            if by_subject[subject] and len(picks) < target:
                picks.append(by_subject[subject].pop(0).key)
    return picks


REASONS = {
    "en": {
        "diagnostic": "A short diagnostic across your subjects, so the plan starts from what you actually know.",
        "retention_due": "Your level in {skill} went up recently. A new problem now shows whether it stuck.",
        "stale": "It has been {days} days since {skill} was last checked. A fresh problem shows whether the level still holds.",
        "core_gap": "{skill} is a core skill for your target role, and you are at level {level} of the {required} it needs.",
        "gap": "You are at level {level} in {skill}; the role asks for {required}.",
        "unassessed": "We have no evidence on {skill} yet. One question tells us where to start.",
        "keep_sharp": "{skill} is in good shape. A quick one keeps it that way.",
        "simulation": "A full interview simulation across your main skills, to practice under real conditions.",
    },
    "he": {
        "diagnostic": "אבחון קצר על פני הנושאים שלכם, כדי שהתוכנית תתחיל ממה שאתם באמת יודעים.",
        "retention_due": "הרמה שלכם ב-{skill} עלתה לאחרונה. בעיה חדשה עכשיו תראה אם זה נשאר.",
        "stale": "עברו {days} ימים מאז ש-{skill} נבדקה לאחרונה. בעיה חדשה תראה אם הרמה עדיין מחזיקה.",
        "core_gap": "{skill} היא מיומנות ליבה לתפקיד היעד, ואתם ברמה {level} מתוך {required} שנדרשת.",
        "gap": "אתם ברמה {level} ב-{skill}; התפקיד דורש {required}.",
        "unassessed": "עדיין אין לנו מידע על {skill}. שאלה אחת תראה מאיפה להתחיל.",
        "keep_sharp": "{skill} במצב טוב. שאלה קצרה תשמור על זה.",
        "simulation": "סימולציית ראיון מלאה על המיומנויות המרכזיות, כדי לתרגל בתנאים אמיתיים.",
    },
}


def reason_text(activity: Activity, language: str, skill_labels: dict[str, str] | None = None) -> str:
    """Plain-language reason shown to the user. Cites real history and stays general when evidence is thin."""
    templates = REASONS.get(language, REASONS["en"])
    facts = dict(activity.reason_facts)
    code = activity.reason_code
    if code in ("core_gap", "gap") and facts.get("level") is None:
        code = "unassessed"
    key = facts.get("skill")
    facts["skill"] = (skill_labels or {}).get(key, key) if key else ""
    return templates.get(code, templates["unassessed"]).format(**{"level": "", "required": "", "days": "", **facts})
