"""What to practise next, decided from the evaluation just made (AI_Engine_Spec §3, §4.11 in miniature).

    WEAK    -> reinforce: the same skill, an easier or equal question, unseen
    PARTIAL -> consolidate: the same skill at the same difficulty, unseen; else advance
    STRONG  -> advance: the next weakest skill the plan cares about, at its entry difficulty

The choice is deterministic and explained in the practice language. It never invents a
question: candidates are the servable bank questions the caller passes in.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.engine import scores
from app.schemas.bank import BankQuestion
from app.schemas.engine import Band, SkillState

REASONS = {
    "en": {
        "reinforce": "Your answer showed a gap in {skill}; this question practises the same idea from a simpler angle.",
        "consolidate": "You were close on {skill}; one more question at this level will settle it.",
        "advance": "{skill} looks solid for now; {next_skill} is the next skill your role plan weights most.",
        "explore": "Nothing is pending on {skill}; {next_skill} has not been practised yet.",
    },
    "he": {
        "reinforce": "התשובה חשפה פער ב-{skill}; השאלה הזו מתרגלת את אותו רעיון מזווית פשוטה יותר.",
        "consolidate": "הייתם קרובים ב-{skill}; עוד שאלה ברמה הזו תייצב את זה.",
        "advance": "{skill} נראה יציב כרגע; {next_skill} היא המיומנות הבאה במשקל הגבוה ביותר בתוכנית התפקיד.",
        "explore": "אין דבר פתוח ב-{skill}; {next_skill} עדיין לא תורגלה.",
    },
}


@dataclass(frozen=True)
class Suggestion:
    key: str
    skill: str
    difficulty: int
    why: str                                   # reinforce | consolidate | advance | explore
    reason: str


def _difficulty_now(state: SkillState | None, required_level: int) -> int:
    level = state.provisional_level if state is not None and state.provisional_level else required_level
    return max(1, scores.min_difficulty_for_level(level))


def _pick(candidates: list[BankQuestion], *, skill: str, target: int, seen: set[str], exclude: str,
          window: tuple[int, int]) -> BankQuestion | None:
    low, high = window
    pool = [q for q in candidates if q.key != exclude and q.key not in seen and q.primary_skill == skill
            and low <= q.difficulty <= high]
    if not pool:
        return None
    return min(pool, key=lambda q: (abs(q.difficulty - target), q.key))


def suggest(*, current: BankQuestion, band: Band | None, states: dict[str, SkillState], candidates: list[BankQuestion],
            seen: set[str], required_levels: dict[str, int], skill_weights: dict[str, float],
            skill_labels: dict[str, str], language: str, difficulty_ceiling: int = 10) -> Suggestion | None:
    texts = REASONS.get(language, REASONS["en"])
    skill = current.primary_skill
    label = skill_labels.get(skill, skill)
    here = current.difficulty

    if band == Band.WEAK:
        pick = _pick(candidates, skill=skill, target=max(1, here - 1), seen=seen, exclude=current.key, window=(1, here))
        if pick:
            return Suggestion(pick.key, skill, pick.difficulty, "reinforce", texts["reinforce"].format(skill=label))
    if band in (Band.WEAK, Band.PARTIAL):
        pick = _pick(candidates, skill=skill, target=here, seen=seen, exclude=current.key, window=(max(1, here - 1), here + 1))
        if pick:
            why = "reinforce" if band == Band.WEAK else "consolidate"
            return Suggestion(pick.key, skill, pick.difficulty, why, texts[why].format(skill=label))

    # advance: the skill the plan weights most among those below their required level, then any unpractised one
    covered = {q.primary_skill for q in candidates if q.key not in seen and q.key != current.key}
    def gap(k: str) -> float:
        s = states.get(k)
        level = s.provisional_level if s is not None and s.provisional_level else 0
        return max(0, required_levels.get(k, 2) - level)
    ranked = sorted((k for k in covered if k != skill), key=lambda k: (-gap(k) * skill_weights.get(k, 0.05), -skill_weights.get(k, 0.05), k))
    for next_skill in ranked:
        target = min(difficulty_ceiling, _difficulty_now(states.get(next_skill), required_levels.get(next_skill, 2)))
        pick = _pick(candidates, skill=next_skill, target=target, seen=seen, exclude=current.key, window=(1, 10))
        if pick:
            why = "advance" if states.get(next_skill) is not None and states[next_skill].turns else "explore"
            return Suggestion(pick.key, next_skill, pick.difficulty, why,
                              texts[why].format(skill=label, next_skill=skill_labels.get(next_skill, next_skill)))
    # last resort: anything unseen on the same skill
    pick = _pick(candidates, skill=skill, target=here, seen=seen, exclude=current.key, window=(1, 10))
    if pick:
        return Suggestion(pick.key, skill, pick.difficulty, "consolidate", texts["consolidate"].format(skill=label))
    return None
