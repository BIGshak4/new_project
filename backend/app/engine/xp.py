"""XP: a motivation layer computed on read from results the engine already stored.

Nothing here touches how an answer is evaluated or how a level is computed. XP is a pure
function of what a scored answer already carries (band, question difficulty, the hints seen
and whether the reference was revealed before the answer, whether it was a follow-up or an
interview turn), summed over the answers on record. No table, no migration: the same
stored rows always give the same XP.

    answer_xp(band, difficulty, ...)     one scored answer -> XP (int, at least 1)
    split_by_skill(xp, links)            the answer's XP over the question's skill links
    streak_days(days, today)             consecutive UTC days with a scored answer, ending today or yesterday
    level_progress(level, level_score)   0..1 fill toward the next level, from the engine's own level score
    summarise(answers, today)            totals: all time, today, streak, per skill
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, timedelta

BAND_XP = {"STRONG": 20, "PARTIAL": 10, "WEAK": 4}
HINT_PENALTY = 0.2            # each hint seen before the answer takes a fifth off ...
HINT_FLOOR = 0.4              # ... but never more than 60 % in total
REFERENCE_FACTOR = 0.25       # the reference solution was revealed before the answer
FOLLOW_UP_FACTOR = 0.5        # a follow-up answer counts half
INTERVIEW_FACTOR = 1.5        # an interview turn is worth more: no reference, the clock running
MIN_XP = 1                    # any scored answer is worth something


def difficulty_factor(difficulty: int) -> float:
    """1.0 at difficulty 1, 2.0 at difficulty 10, linear between."""
    d = max(1, min(10, int(difficulty or 1)))
    return 1 + (d - 1) / 9


def hint_factor(hints_seen: int) -> float:
    return max(HINT_FLOOR, 1 - HINT_PENALTY * max(0, int(hints_seen or 0)))


def answer_xp(band: str | None, *, difficulty: int, hints_seen: int = 0, reference_seen: bool = False,
              follow_up: bool = False, interview: bool = False) -> int:
    """XP for one scored answer. 0 when there is no band (unscored, failed, still evaluating)."""
    base = BAND_XP.get(str(band).upper()) if band else None
    if base is None:
        return 0
    value = base * difficulty_factor(difficulty) * hint_factor(hints_seen)
    if reference_seen:
        value *= REFERENCE_FACTOR
    if follow_up:
        value *= FOLLOW_UP_FACTOR
    if interview:
        value *= INTERVIEW_FACTOR
    return max(MIN_XP, math.floor(value + 0.5))          # half up, like the engine's rounding (2.5 -> 3)


def split_by_skill(xp: int, links: Iterable[tuple[str, float]]) -> dict[str, int]:
    """The answer's XP over the question's skill links by weight; whole numbers that add up to `xp`
    (largest remainders get the leftover points). One skill with weight 1.0 gets everything."""
    pairs = [(key, float(weight)) for key, weight in links if weight and weight > 0]
    if xp <= 0 or not pairs:
        return {}
    total = sum(weight for _, weight in pairs)
    exact = [(key, xp * weight / total) for key, weight in pairs]
    out = {key: int(value) for key, value in exact}
    leftover = xp - sum(out.values())
    for key, _ in sorted(exact, key=lambda kv: (-(kv[1] - int(kv[1])), kv[0]))[:leftover]:
        out[key] += 1
    return out


def streak_days(days: Iterable[str | date], today: date) -> int:
    """Consecutive days with at least one scored answer, counted back from today; a day not yet practised
    does not break the streak, so a run ending yesterday still counts. 0 when neither today nor yesterday
    has an answer."""
    seen = {d if isinstance(d, date) else date.fromisoformat(str(d)[:10]) for d in days}
    if not seen:
        return 0
    cursor = today if today in seen else today - timedelta(days=1)
    if cursor not in seen:
        return 0
    n = 0
    while cursor in seen:
        n += 1
        cursor -= timedelta(days=1)
    return n


def level_progress(level: int | None, level_score: float | None) -> float:
    """How far the engine's level score sits inside the current level, 0..1.

    `scores.questioned_level` rounds `level_score` half-up to the level: level L spans scores
    [L - 0.5, L + 0.5). The fill is the distance covered inside that span. A level capped below its
    score (a level-3 hint, a core misconception) shows a full bar: the score is there, the cap is what
    holds it. Nothing assessed yet: 0. Read-only: the level itself is the engine's, unchanged."""
    if level is None or level_score is None:
        return 0.0
    if level >= 5:
        return 1.0
    return max(0.0, min(1.0, float(level_score) - (int(level) - 0.5)))


@dataclass
class ScoredAnswer:
    """What XP needs from one stored answer: the store hands these over, the engine never sees them."""

    day: str                                       # UTC date, ISO
    band: str | None
    difficulty: int
    hints_seen: int = 0
    reference_seen: bool = False
    follow_up: bool = False
    interview: bool = False
    skills: list[tuple[str, float]] = field(default_factory=list)   # (skill key, link weight)

    @property
    def xp(self) -> int:
        return answer_xp(self.band, difficulty=self.difficulty, hints_seen=self.hints_seen,
                         reference_seen=self.reference_seen, follow_up=self.follow_up, interview=self.interview)


@dataclass
class XpSummary:
    total: int = 0
    today: int = 0
    streak: int = 0
    per_skill: dict[str, int] = field(default_factory=dict)


def summarise(answers: Iterable[ScoredAnswer], today: date) -> XpSummary:
    out = XpSummary()
    days: set[str] = set()
    today_iso = today.isoformat()
    for answer in answers:
        earned = answer.xp
        if earned <= 0:
            continue
        out.total += earned
        if answer.day == today_iso:
            out.today += earned
        days.add(answer.day)
        # a follow-up is evidence on the question's primary skill only (as the engine records it); the readers put
        # the primary skill first
        links = answer.skills[:1] if answer.follow_up and answer.skills else answer.skills
        for key, part in split_by_skill(earned, [(k, 1.0) for k, _ in links] if answer.follow_up else links).items():
            out.per_skill[key] = out.per_skill.get(key, 0) + part
    out.streak = streak_days(days, today)
    return out


def from_rows(rows: Iterable[dict]) -> list[ScoredAnswer]:
    """Store rows -> ScoredAnswer. A row: {day, band, difficulty, hints_seen, reference_seen, turn | follow_up,
    interview, skills: [[key, weight], ...]}."""
    out = []
    for r in rows:
        follow_up = bool(r.get("follow_up")) if "follow_up" in r else int(r.get("turn") or 0) > 0
        out.append(ScoredAnswer(day=str(r["day"])[:10], band=r.get("band"), difficulty=int(r.get("difficulty") or 1),
                                hints_seen=int(r.get("hints_seen") or 0), reference_seen=bool(r.get("reference_seen")),
                                follow_up=follow_up, interview=bool(r.get("interview")),
                                skills=[(str(k), float(w)) for k, w in (r.get("skills") or [])]))
    return out
