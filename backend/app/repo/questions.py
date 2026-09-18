"""Questions, read from the database.

The database is the runtime source of question content: that is where review and
publication state live, and where Harel's app reads. `seed_db.py` writes every field
the engine needs; this module reads them back into the engine's `BankQuestion`.

Two shapes leave this module:

    QuestionSummary / QuestionDetail   safe by construction: prompt, code, choices,
                                       difficulty, minutes. Never the reference solution,
                                       the hint texts, the correct choice or the rubric.
    BankQuestion                       the full engine object, used server-side only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db
from app.schemas.bank import BankQuestion, CommonError, QuestionSkillLink, QuestionText, RubricCriterion
from app.schemas.engine import Archetype

SERVABLE_STATUSES = ("published",)
DEVELOPMENT_STATUSES = ("published", "in_review")


class QuestionSummary(BaseModel):
    id: str
    key: str
    title: str
    subject: str
    format: str
    difficulty: int
    estimated_minutes: int | None
    practice_modes: list[str]
    language: str                              # the language the text is actually in
    languages: list[str]                       # languages with a parity-checked text
    status: str
    hint_count: int
    has_reference: bool = True
    has_check: bool = False


class QuestionDetail(QuestionSummary):
    prompt: str                                # prompt plus shared code block
    requirements: str
    choices: list[str] | None = None
    starter_code: str | None = None
    code_language: str | None = None


@dataclass
class LoadedQuestion:
    id: uuid.UUID
    question: BankQuestion
    version: int


def _allowed_statuses(allow_in_review: bool) -> tuple[str, ...]:
    return DEVELOPMENT_STATUSES if allow_in_review else SERVABLE_STATUSES


async def _skill_keys(connection: AsyncConnection) -> dict[uuid.UUID, str]:
    skill = await db.table("skill")
    rows = await connection.execute(select(skill.c.id, skill.c.key))
    return {row.id: row.key for row in rows}


async def _tip_keys(connection: AsyncConnection) -> dict[str, str]:
    tips = await db.table("tips_library")
    rows = await connection.execute(select(tips.c.id, tips.c.key))
    return {str(row.id): row.key for row in rows}


def _bank_question(row, translations: list, links: list, skill_keys: dict, tip_keys: dict) -> BankQuestion:
    """The inverse of seed_db's row construction."""
    assets = dict(row.assets or {})
    archetype = assets.pop("archetype", None) or Archetype.CONCEPTUAL.value
    choices = row.choices or {}
    texts: dict[str, QuestionText] = {}
    for t in translations:
        texts[t.language] = QuestionText(
            title=(assets.get("titles") or {}).get(t.language, ""), prompt=t.prompt,
            requirements=t.requirements or row.requirements, reference_solution=t.reference_solution or row.reference_solution,
            hints=list(t.hints or []), common_errors=dict(t.common_errors or {}),
            accepted_approaches=list(row.accepted_approaches or []) if t.language == "en" else list(row.accepted_approaches or []),
            choices=list(t.choices) if t.choices else None, parity_checked=bool(t.parity_checked),
            parity_checked_by=t.parity_checked_by)
    return BankQuestion(
        key=row.key, version=row.version, status=row.status, origin=row.origin, format=row.format,
        practice_modes=list(row.practice_modes), subject=skill_keys[row.subject_id], difficulty=row.difficulty,
        estimated_minutes=row.estimated_minutes, archetype=archetype,
        skills=[QuestionSkillLink(skill=skill_keys[link.skill_id], weight=float(link.weight), primary=bool(link.is_primary))
                for link in links],
        rubric=[RubricCriterion.model_validate(c) for c in (row.rubric or {}).get("criteria", [])],
        common_errors=[CommonError(key=e["key"], core=bool(e.get("core")), skill=e.get("skill"),
                                   tip_key=tip_keys.get(str(e.get("tip_id"))) if e.get("tip_id") else None)
                       for e in (row.common_errors or [])],
        deterministic_check=row.deterministic_check, correct_choice=choices.get("correct_index"),
        choice_misconceptions=choices.get("misconceptions"), assets=assets,
        source_name=row.source_name, source_url=row.source_url, license=row.license, reuse_status=row.reuse_status,
        attribution_text=row.attribution_text, reviewed_by=row.reviewed_by,
        reviewed_at=row.reviewed_at.isoformat() if row.reviewed_at else None, review_notes=row.review_notes,
        exposure_risk=row.exposure_risk, times_served=row.times_served, translations=texts)


async def load_question(connection: AsyncConnection, *, key: str | None = None, question_id: uuid.UUID | None = None,
                        allow_in_review: bool = False) -> LoadedQuestion | None:
    """The full engine object for one question, or None when it does not exist or may not be served."""
    question, translation, link = (await db.table("question"), await db.table("question_translation"),
                                   await db.table("question_skill"))
    condition = question.c.key == key if key is not None else question.c.id == question_id
    row = (await connection.execute(select(question).where(condition))).first()
    if row is None or row.status not in _allowed_statuses(allow_in_review):
        return None
    translations = (await connection.execute(
        select(translation).where(translation.c.question_id == row.id).order_by(translation.c.language))).all()
    links = (await connection.execute(
        select(link).where(link.c.question_id == row.id).order_by(link.c.is_primary.desc(), link.c.weight.desc()))).all()
    if not translations or not any(bool(lk.is_primary) for lk in links):
        return None                                  # not enriched yet: the engine cannot run it
    bank = _bank_question(row, translations, links, await _skill_keys(connection), await _tip_keys(connection))
    return LoadedQuestion(id=row.id, question=bank, version=row.version)


def summary(loaded: LoadedQuestion, language: str) -> QuestionSummary:
    q = loaded.question
    text_language = language if language in q.translations else "en" if "en" in q.translations else next(iter(q.translations))
    text = q.translations[text_language]
    return QuestionSummary(
        id=str(loaded.id), key=q.key, title=text.title or (q.assets.get("titles") or {}).get("en", q.key),
        subject=q.subject, format=q.format, difficulty=q.difficulty, estimated_minutes=q.estimated_minutes,
        practice_modes=list(q.practice_modes), language=text_language, languages=q.languages_ready(), status=q.status,
        hint_count=len(text.hints), has_check=q.deterministic_check is not None)


def detail(loaded: LoadedQuestion, language: str) -> QuestionDetail:
    base = summary(loaded, language)
    q = loaded.question
    text = q.translations[base.language]
    return QuestionDetail(
        **base.model_dump(), prompt=q.prompt_with_code(base.language), requirements=text.requirements,
        choices=list(text.choices) if text.choices else None, starter_code=q.assets.get("starter_code"),
        code_language=q.assets.get("code_language"))


async def list_questions(connection: AsyncConnection, *, language: str, allow_in_review: bool = False,
                         subject: str | None = None) -> list[QuestionSummary]:
    """Every servable, enriched question as a safe summary."""
    question, link = await db.table("question"), await db.table("question_skill")
    statuses = _allowed_statuses(allow_in_review)
    enriched = select(link.c.question_id).where(link.c.is_primary.is_(True))
    rows = (await connection.execute(
        select(question.c.id).where(question.c.status.in_(statuses), question.c.id.in_(enriched))
        .order_by(question.c.difficulty, question.c.key))).all()
    out = []
    for row in rows:
        loaded = await load_question(connection, question_id=row.id, allow_in_review=allow_in_review)
        if loaded is None or (subject and loaded.question.subject != subject):
            continue
        out.append(summary(loaded, language))
    return out
