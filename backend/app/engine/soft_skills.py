"""Soft skills and the improvement gradient, read from what the judge already stored (Shaked, 2026-10-18).

Backend-only data: nothing here reaches the API or the screens. Every scored answer and interview turn carries the
judge's five soft dimensions (clarity, structure, trade-off reasoning, risk awareness, hedging) and its behaviour
tags; this module turns them into seven soft skills with a level in words, a slope per skill ("points per week"), and
one overall improvement word per candidate. Pure functions: the service hands in the evidence, nothing is written.
The hard skills' gradient comes from the profile's level history the same way.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

SOFT_SKILLS: dict[str, dict[str, str]] = {
    "analytical_reasoning": {"en": "Analytical reasoning", "he": "חשיבה אנליטית"},
    "structured_explanation": {"en": "Structured explanation", "he": "הסבר מובנה"},
    "tradeoff_reasoning": {"en": "Trade-off reasoning", "he": "שיקולי תמורה"},
    "edge_case_attention": {"en": "Attention to edge cases", "he": "תשומת לב למקרי קצה"},
    "problem_solving_habits": {"en": "Problem-solving habits", "he": "הרגלי פתרון בעיות"},
    "clear_communication": {"en": "Clear communication", "he": "תקשורת ברורה"},
    "calibration": {"en": "Calibration", "he": "כיול ביטחון"},
}
REASONING_SKILLS = {"estimation_sanity_checks", "debugging_methodology", "code_debugging"}   # analytical reasoning's questions
MIN_ANSWERS_FOR_LEVEL = 5          # one answer never labels anyone
MIN_ANSWERS_FOR_SLOPE = 8
MIN_SPAN_DAYS = 7
LEVEL_WINDOW_DAYS = 49             # the hard skills' "expired" horizon
SLOPE_WINDOW_DAYS = 180
HALF_LIFE_DAYS = 21                # a three-week-old answer weighs half (the weeks rule)
LEVEL_THRESHOLDS = (0.30, 0.45, 0.60, 0.78)     # the interview's observed-skill thresholds (ScoreParams)
SLOPE_QUICK, SLOPE_IMPROVING, SLOPE_SLIPPING = 4.0, 1.5, -1.5   # points per week on a 0..100 scale; to tune on pilot data
LEVEL_WORDS = {
    "en": ["Getting started", "First steps", "Foundational", "Proficient", "Advanced"],
    "he": ["בתחילת הדרך", "צעדים ראשונים", "בסיס", "שליטה", "מתקדם"],
}
IMPROVEMENT_WORDS = {
    "en": {"too_early": "Too early to tell", "slipping": "Slipping", "steady": "Steady", "improving": "Improving",
           "improving_quickly": "Improving quickly"},
    "he": {"too_early": "מוקדם מדי לומר", "slipping": "נסיגה", "steady": "יציב", "improving": "משתפר",
           "improving_quickly": "משתפר מהר"},
}


@dataclass
class Evidence:
    """One scored answer or interview turn, as the store hands it over."""

    at: datetime
    evaluation: dict                       # the judge's JSON: correctness, depth, clarity, ..., behavior_signals
    flags: list[str]
    archetype: str | None                  # the question's archetype: conceptual | coding | debugging | design | behavioral
    primary_skill: str | None
    source: str = "practice"               # practice | interview


@dataclass
class SoftSkillAssessment:
    key: str
    label: dict[str, str]
    answers: int                           # relevant answers inside the level window
    mean: float | None                     # faded mean of the per-answer scores, 0..1 (None under the minimum)
    level_rank: int | None                 # 1..5
    level: dict[str, str] | None
    slope_per_week: float | None           # points per week on a 0..100 scale over the slope window
    improvement: str                       # too_early | slipping | steady | improving | improving_quickly
    span_days: int
    latest_at: datetime | None


def _f(value) -> float | None:
    try:
        return None if value is None else max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None


def answer_score(skill: str, ev: Evidence) -> float | None:
    """The per-answer score of one soft skill, or None when this answer says nothing about it."""
    if "off_topic" in ev.flags or "empty_answer" in ev.flags:
        return None
    e = ev.evaluation or {}
    signals = set(e.get("behavior_signals") or [])
    correctness, depth = _f(e.get("correctness")), _f(e.get("depth"))
    if skill == "analytical_reasoning":
        if ev.primary_skill in REASONING_SKILLS or ev.archetype == "debugging":
            return None if correctness is None or depth is None else (correctness + depth) / 2
        return None
    if skill == "structured_explanation":
        return _f(e.get("structure"))
    if skill == "tradeoff_reasoning":
        return _f(e.get("tradeoff_reasoning")) if ev.archetype == "design" else None
    if skill == "edge_case_attention":
        if ev.archetype not in ("design", "debugging"):
            return None
        risk = _f(e.get("risk_awareness"))
        if risk is None:
            return None
        if "considered_edge_cases" in signals:
            risk = min(1.0, risk + 0.15)
        if "ignored_edge_cases" in signals:
            risk = max(0.0, risk - 0.15)
        return risk
    if skill == "problem_solving_habits":
        good = bool(signals & {"stated_assumptions", "asked_clarifying_question", "verified_with_example"})
        bad = "jumped_to_implementation" in signals
        if good and not bad:
            return 1.0
        if bad and not good:
            return 0.0
        return 0.5                                       # neither shown: counted as neutral, so the level reflects frequency
    if skill == "clear_communication":
        return _f(e.get("clarity"))
    if skill == "calibration":
        hedging = _f(e.get("hedging_ratio"))
        if hedging is None or correctness is None:
            return None
        if "overconfident_wrong" in signals:
            return 0.1
        if correctness >= 0.6:
            return 1.0 - 0.6 * hedging                   # committed and right 1.0; hedged throughout while right 0.4
        return 0.3 + 0.4 * hedging                       # wrong: hedging was the honest signal
    raise KeyError(skill)


def fade(age_days: float) -> float:
    return 0.5 ** (max(0.0, age_days) / HALF_LIFE_DAYS)


def level_rank(mean: float) -> int:
    for rank, threshold in enumerate(LEVEL_THRESHOLDS, start=1):
        if mean < threshold:
            return rank
    return 5


def slope_per_week(points: list[tuple[float, float]]) -> float | None:
    """Least-squares slope of (day, score 0..1) points, returned as points per week on a 0..100 scale."""
    if len(points) < 2:
        return None
    n = len(points)
    mx = sum(x for x, _ in points) / n
    my = sum(y for _, y in points) / n
    sxx = sum((x - mx) ** 2 for x, _ in points)
    if sxx == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in points)
    return (sxy / sxx) * 7 * 100


def improvement_key(slope: float | None, answers: int, span_days: int) -> str:
    if slope is None or answers < MIN_ANSWERS_FOR_SLOPE or span_days < MIN_SPAN_DAYS:
        return "too_early"
    if slope >= SLOPE_QUICK:
        return "improving_quickly"
    if slope >= SLOPE_IMPROVING:
        return "improving"
    if slope > SLOPE_SLIPPING:
        return "steady"
    return "slipping"


def _aware(at: datetime) -> datetime:
    return at if at.tzinfo else at.replace(tzinfo=UTC)


def assess(evidence: list[Evidence], now: datetime | None = None) -> list[SoftSkillAssessment]:
    """The seven soft skills from a candidate's evidence: a faded mean inside the level window, a slope over the
    longer window, and the words for both."""
    now = now or datetime.now(UTC)
    out = []
    for key, label in SOFT_SKILLS.items():
        scored: list[tuple[datetime, float]] = []
        for ev in evidence:
            value = answer_score(key, ev)
            if value is not None:
                scored.append((_aware(ev.at), value))
        scored.sort(key=lambda p: p[0])
        in_slope = [(at, v) for at, v in scored if (now - at).days <= SLOPE_WINDOW_DAYS]
        in_level = [(at, v) for at, v in in_slope if (now - at).days <= LEVEL_WINDOW_DAYS]
        mean = rank = level = None
        if len(in_level) >= MIN_ANSWERS_FOR_LEVEL:
            weights = [fade((now - at).total_seconds() / 86400) for at, _ in in_level]
            mean = sum(w * v for w, (_, v) in zip(weights, in_level, strict=True)) / sum(weights)
            rank = level_rank(mean)
            level = {lang: words[rank - 1] for lang, words in LEVEL_WORDS.items()}
        span = (in_slope[-1][0] - in_slope[0][0]).days if len(in_slope) >= 2 else 0
        first = in_slope[0][0] if in_slope else now
        slope = slope_per_week([((at - first).total_seconds() / 86400, v) for at, v in in_slope]) if len(in_slope) >= 2 else None
        out.append(SoftSkillAssessment(key=key, label=label, answers=len(in_level), mean=None if mean is None else round(mean, 3),
                                       level_rank=rank, level=level, slope_per_week=None if slope is None else round(slope, 2),
                                       improvement=improvement_key(slope, len(in_slope), span), span_days=span,
                                       latest_at=in_slope[-1][0] if in_slope else None))
    return out


def hard_skill_gradient(level_history: dict[str, list[dict]], now: datetime | None = None) -> dict[str, dict]:
    """Per hard skill: the slope of its level history (levels 1..5 mapped to 20..100 points) over the slope window."""
    now = now or datetime.now(UTC)
    out: dict[str, dict] = {}
    for key, history in level_history.items():
        points: list[tuple[datetime, float]] = []
        for entry in history or []:
            at, level = entry.get("at"), entry.get("level")
            if at is None or level is None:
                continue
            stamp = _aware(datetime.fromisoformat(at) if isinstance(at, str) else at)
            if (now - stamp).days <= SLOPE_WINDOW_DAYS:
                points.append((stamp, float(level) / 5))
        points.sort(key=lambda p: p[0])
        span = (points[-1][0] - points[0][0]).days if len(points) >= 2 else 0
        first = points[0][0] if points else now
        slope = slope_per_week([((at - first).total_seconds() / 86400, v) for at, v in points]) if len(points) >= 2 else None
        out[key] = {"levels": len(points), "span_days": span, "slope_per_week": None if slope is None else round(slope, 2),
                    "improvement": improvement_key(slope, len(points), span) if len(points) >= 2 else "too_early"}
    return out


def overall_improvement(soft: list[SoftSkillAssessment], hard: dict[str, dict], weights: dict[str, float]) -> dict:
    """One word per candidate: the weighted mean slope of every skill with enough evidence (hard skills by their plan
    weight, the seven soft skills sharing the same total as one plan). None of it reaches a screen."""
    pairs: list[tuple[float, float]] = []
    total_hard = sum(weights.get(k, 0.0) for k, g in hard.items() if g["improvement"] != "too_early") or 1.0
    for key, g in hard.items():
        if g["improvement"] != "too_early":
            pairs.append((weights.get(key, 0.0) / total_hard, g["slope_per_week"]))
    judged_soft = [s for s in soft if s.improvement != "too_early"]
    for s in judged_soft:
        pairs.append((1.0 / len(judged_soft), s.slope_per_week))
    if not pairs:
        return {"slope_per_week": None, "improvement": "too_early", "skills_judged": 0}
    slope = sum(w * v for w, v in pairs) / sum(w for w, _ in pairs)
    return {"slope_per_week": round(slope, 2), "improvement": improvement_key(slope, MIN_ANSWERS_FOR_SLOPE, MIN_SPAN_DAYS),
            "skills_judged": len(pairs)}
