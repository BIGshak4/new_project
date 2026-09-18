"""Bank-first question selection (AI_Engine_Spec §1.2).

Order of use: a published bank question the user has not seen, then an unseen
variation of a seen question, then (returning None) an AI-generated question,
which the caller labels as generated.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.bank import BankQuestion
from app.schemas.engine import Archetype

FORMATS_FOR_ARCHETYPE: dict[Archetype, set[str]] = {
    Archetype.CONCEPTUAL: {"short_answer", "explain", "multiple_choice", "truth_table"},
    Archetype.CODING: {"code", "hdl"},
    Archetype.DEBUGGING: {"hdl", "code", "waveform", "explain", "multiple_choice"},
    Archetype.DESIGN: {"construct", "hdl", "explain", "truth_table", "waveform"},
    Archetype.BEHAVIORAL: {"explain", "short_answer"},
}


@dataclass(frozen=True)
class Selection:
    question: BankQuestion
    familiarity: str                   # new | seen_variation
    relaxed: list[str]                 # which preferences had to be dropped to find it


def _servable(question: BankQuestion, *, mode: str, language: str, allow_in_review: bool, require_parity: bool) -> bool:
    if question.status != "published" and not (allow_in_review and question.status in ("in_review", "draft")):
        return False
    if mode not in question.practice_modes:
        return False
    text = question.translations.get(language)
    if text is None:
        return False
    return text.parity_checked or not require_parity


def select_question(questions: list[BankQuestion], *, skill: str, difficulty: int, mode: str, language: str,
                    seen_keys: set[str] | None = None, archetype: Archetype | None = None,
                    allow_in_review: bool = False, require_parity: bool = True,
                    difficulty_window: int = 1) -> Selection | None:
    """The best bank question for a fixed skill, difficulty and mode, or None if the bank has no fit."""
    seen = seen_keys or set()
    pool = [q for q in questions if q.primary_skill == skill
            and _servable(q, mode=mode, language=language, allow_in_review=allow_in_review, require_parity=require_parity)]
    if not pool:
        return None

    def family(question: BankQuestion) -> str:
        return question.variation_of or question.key

    seen_families = {family(q) for q in pool if q.key in seen} | {k for k in seen}

    def rank(question: BankQuestion):
        return (abs(question.difficulty - difficulty), question.times_served, question.key)

    in_window = [q for q in pool if abs(q.difficulty - difficulty) <= difficulty_window]
    fits = [q for q in in_window if archetype is None or q.format in FORMATS_FOR_ARCHETYPE.get(archetype, set())]

    for candidates, relaxed in ((fits, []), (in_window, ["archetype"])):
        # 1. never seen, and no member of its family seen either
        fresh = [q for q in candidates if q.key not in seen and family(q) not in seen_families]
        if fresh:
            return Selection(min(fresh, key=rank), "new", relaxed)
        # 2. an unseen variation of something already seen
        variations = [q for q in candidates if q.key not in seen]
        if variations:
            return Selection(min(variations, key=rank), "seen_variation", relaxed)
    return None


def coverage_by_skill(questions: list[BankQuestion], *, language: str, allow_in_review: bool = False,
                      require_parity: bool = True) -> dict[str, dict[str, int]]:
    """How many servable questions the bank holds per skill and mode. An input to the Plan Router."""
    coverage: dict[str, dict[str, int]] = {}
    for question in questions:
        for mode in question.practice_modes:
            if _servable(question, mode=mode, language=language, allow_in_review=allow_in_review,
                         require_parity=require_parity):
                per_skill = coverage.setdefault(question.primary_skill, {})
                per_skill[mode] = per_skill.get(mode, 0) + 1
    return coverage
