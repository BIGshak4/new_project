"""What to practise next, decided from the evaluation just made (AI_Engine_Spec §3, §4.11 in miniature).

The suggestion starts from what was actually hard in this attempt:

    a known misconception was hit  -> the skill that misconception undermines; its bank explanation
                                      becomes `focus` ("what was hard here")
    WEAK without a named mistake   -> reinforce: the same skill, an easier or equal question, unseen
    PARTIAL                        -> consolidate: the same skill at the same difficulty, unseen
    STRONG                         -> advance: the next weakest skill the plan cares about

Follow-up answers count: the weakest band across the main answer and the follow-ups decides.
A candidate question counts for a skill when it examines it as its primary or a secondary skill,
so a struggle with the secondary skill of one question can lead to a question built on it.
The choice is deterministic and explained in the practice language. It never invents a question:
candidates are the servable bank questions the caller passes in.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.engine import scores
from app.schemas.bank import BankQuestion
from app.schemas.engine import Band, SkillState

REASONS = {
    "en": {
        "struggle": "The next question practises {skill} again, from a simpler angle, so this idea settles.",
        "struggle_other": "That mistake comes from {skill}; the next question practises it from a simpler angle.",
        "reinforce": "Your answer showed a gap in {skill}; this question practises the same idea from a simpler angle.",
        "consolidate": "You were close on {skill}; one more question at this level will settle it.",
        "advance": "{skill} looks solid for now; {next_skill} is where your plan has the most to gain.",
        "advance_after_weak": "No other question on {skill} is available right now; {next_skill} is next in your plan.",
        "map": "You have enough on {skill} for now; {next_skill} weighs most in your plan and has no evidence yet.",
        "explore": "Nothing is pending on {skill}; {next_skill} has not been practised yet.",
        "explore_after_weak": "No other question on {skill} is available right now; {next_skill} has not been practised yet.",
        "same_skill": "Nothing else is waiting in your plan right now; one more on {skill} at this level.",
    },
    "he": {
        "struggle": "השאלה הבאה מתרגלת שוב {skill}, מזווית פשוטה יותר, כדי שהרעיון הזה יתייצב.",
        "struggle_other": "הטעות הזו נובעת מ-{skill}; השאלה הבאה מתרגלת אותה מזווית פשוטה יותר.",
        "reinforce": "התשובה חשפה פער ב-{skill}; השאלה הזו מתרגלת את אותו רעיון מזווית פשוטה יותר.",
        "consolidate": "הייתם קרובים ב-{skill}; עוד שאלה ברמה הזו תייצב את זה.",
        "advance": "{skill} נראה יציב כרגע; ב-{next_skill} יש לתוכנית שלכם הכי הרבה מה להרוויח.",
        "advance_after_weak": "אין כרגע שאלה נוספת על {skill}; {next_skill} היא הבאה בתוכנית שלכם.",
        "map": "יש מספיק על {skill} בינתיים; {next_skill} היא הכבדה ביותר בתוכנית ועדיין בלי עדות.",
        "explore": "אין דבר פתוח ב-{skill}; {next_skill} עדיין לא תורגלה.",
        "explore_after_weak": "אין כרגע שאלה נוספת על {skill}; {next_skill} עדיין לא תורגלה.",
        "same_skill": "שום דבר אחר לא מחכה בתוכנית כרגע; עוד אחת על {skill} ברמה הזו.",
    },
}

_BAND_ORDER = (Band.WEAK, Band.PARTIAL, Band.STRONG)


@dataclass(frozen=True)
class Struggle:
    """One named difficulty seen in this attempt: the skill it undermines and the bank's explanation."""

    key: str
    skill: str
    text: str
    core: bool = False


@dataclass(frozen=True)
class Suggestion:
    key: str
    skill: str
    difficulty: int
    why: str                                   # reinforce | consolidate | advance | explore | map | same_skill
    reason: str
    focus: str | None = None                   # what was hard in this attempt, in the practice language


EARLY_COVERAGE = 0.7             # below this share of plan skills with evidence, mapping comes before consolidating


def _difficulty_now(state: SkillState | None, required_level: int) -> int:
    level = state.provisional_level if state is not None and state.provisional_level else required_level
    return max(1, scores.min_difficulty_for_level(level))


def _examines(question: BankQuestion, skill: str) -> bool:
    return any(link.skill == skill for link in question.skills)


def _pick(candidates: list[BankQuestion], *, skill: str, target: int, seen: set[str], exclude: str,
          window: tuple[int, int]) -> BankQuestion | None:
    """The closest unseen question on the skill: primary-skill questions first, then ones that examine it."""
    low, high = window
    pool = [q for q in candidates if q.key != exclude and q.key not in seen and low <= q.difficulty <= high
            and _examines(q, skill)]
    if not pool:
        return None
    return min(pool, key=lambda q: (q.primary_skill != skill, abs(q.difficulty - target), q.key))


def _sentence(text: str) -> str:
    text = " ".join(text.split())
    return text if not text or text[-1] in ".!?" else text + "."


def suggest(*, current: BankQuestion, band: Band | None, states: dict[str, SkillState], candidates: list[BankQuestion],
            seen: set[str], required_levels: dict[str, int], skill_weights: dict[str, float],
            skill_labels: dict[str, str], language: str, difficulty_ceiling: int = 10,
            struggles: list[Struggle] | None = None, follow_up_bands: list[Band] | None = None) -> Suggestion | None:
    texts = REASONS.get(language, REASONS["en"])
    primary = current.primary_skill
    here = current.difficulty
    bands = [b for b in [band, *(follow_up_bands or [])] if b is not None]
    weakest = min(bands, key=_BAND_ORDER.index) if bands else None

    # 1. a named difficulty: the skill it undermines, explained in the bank's own words
    for focus in sorted(struggles or [], key=lambda s: (not s.core, s.skill != primary, s.key)):
        if not focus.text.strip():
            continue
        label = skill_labels.get(focus.skill, focus.skill)
        pick = (_pick(candidates, skill=focus.skill, target=max(1, here - 1), seen=seen, exclude=current.key, window=(1, here))
                or _pick(candidates, skill=focus.skill, target=here, seen=seen, exclude=current.key, window=(1, here + 1)))
        if pick:
            # "again" only when the undermined skill is the one just practised (task 10, 2026-10-15)
            wording = texts["struggle" if focus.skill == primary else "struggle_other"]
            return Suggestion(pick.key, focus.skill, pick.difficulty, "reinforce", wording.format(skill=label),
                              focus=_sentence(focus.text))

    label = skill_labels.get(primary, primary)
    # 1b. early in the plan (Shaked, 2026-10-04): once this skill has enough evidence (two scored answers, the
    #     follow-up counts), the heaviest skill with no evidence comes next, so the strength card fills in the first
    #     days; a WEAK answer still reinforces the same skill first
    current_state = states.get(primary)
    plan_keys = set(skill_weights) or set(states)
    with_evidence = {k for k, s in states.items() if s.turns}
    early = plan_keys and len(with_evidence & plan_keys) / len(plan_keys) < EARLY_COVERAGE
    if early and weakest != Band.WEAK and current_state is not None and current_state.turns >= 2:
        unseen = {q.primary_skill for q in candidates if q.key not in seen and q.key != current.key} - with_evidence - {primary}
        for next_skill in sorted(unseen, key=lambda k: (-skill_weights.get(k, 0.05), k)):
            pick = _pick(candidates, skill=next_skill, target=_difficulty_now(None, required_levels.get(next_skill, 2)),
                         seen=seen, exclude=current.key, window=(1, 10))
            if pick:
                return Suggestion(pick.key, next_skill, pick.difficulty, "map",
                                  texts["map"].format(skill=label, next_skill=skill_labels.get(next_skill, next_skill)))

    # 2. the band alone: reinforce or consolidate the main skill
    if weakest == Band.WEAK:
        pick = _pick(candidates, skill=primary, target=max(1, here - 1), seen=seen, exclude=current.key, window=(1, here))
        if pick:
            return Suggestion(pick.key, primary, pick.difficulty, "reinforce", texts["reinforce"].format(skill=label))
    if weakest in (Band.WEAK, Band.PARTIAL):
        pick = _pick(candidates, skill=primary, target=here, seen=seen, exclude=current.key, window=(max(1, here - 1), here + 1))
        if pick:
            why = "reinforce" if weakest == Band.WEAK else "consolidate"
            return Suggestion(pick.key, primary, pick.difficulty, why, texts[why].format(skill=label))

    # 3. advance: the skill the plan weights most among those below their required level, then any unpractised one
    covered = {q.primary_skill for q in candidates if q.key not in seen and q.key != current.key}

    def gap(k: str) -> float:
        s = states.get(k)
        level = s.provisional_level if s is not None and s.provisional_level else 0
        return max(0, required_levels.get(k, 2) - level)
    ranked = sorted((k for k in covered if k != primary),
                    key=lambda k: (-gap(k) * skill_weights.get(k, 0.05), -skill_weights.get(k, 0.05), k))
    for next_skill in ranked:
        target = min(difficulty_ceiling, _difficulty_now(states.get(next_skill), required_levels.get(next_skill, 2)))
        pick = _pick(candidates, skill=next_skill, target=target, seen=seen, exclude=current.key, window=(1, 10))
        if pick:
            why = "advance" if states.get(next_skill) is not None and states[next_skill].turns else "explore"
            # after a weak or partial answer the coach moved on only because the skill has no other question: say
            # that, never "looks solid" (task 10, 2026-10-15)
            wording = texts[why + "_after_weak"] if weakest in (Band.WEAK, Band.PARTIAL) else texts[why]
            return Suggestion(pick.key, next_skill, pick.difficulty, why,
                              wording.format(skill=label, next_skill=skill_labels.get(next_skill, next_skill)))
    # last resort: anything unseen on the same skill; its own words, "you were close" would be false after a strong answer
    pick = _pick(candidates, skill=primary, target=here, seen=seen, exclude=current.key, window=(1, 10))
    if pick:
        return Suggestion(pick.key, primary, pick.difficulty, "same_skill", texts["same_skill"].format(skill=label))
    return None
