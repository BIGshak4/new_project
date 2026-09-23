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

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db
from app.repo import cache
from app.schemas.bank import BankQuestion, CommonError, QuestionSkillLink, QuestionText, RubricCriterion
from app.schemas.engine import Archetype

SERVABLE_STATUSES = ("published", "trial")           # trial: checked live by the founders, badged in the app
DEVELOPMENT_STATUSES = ("published", "trial", "in_review")


class CompanyTag(BaseModel):
    """'Seen at company X' by n candidates. Aggregated; never who."""

    slug: str
    name: str
    count: int


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
    reviewed: bool = False                     # published, or on trial by the founders' choice: what the coach may suggest
    trial: bool = False                        # "on trial": being checked live before publication; the app badges it
    job_types: list[str] = Field(default_factory=list)          # job types this question is relevant to (keys)
    companies: list[CompanyTag] = Field(default_factory=list)   # "I saw it at ..." tags, most reported first
    relevance: float | None = None             # how well it fits the requested job type (set only when one is asked)


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
    async def load():
        skill = await db.table("skill")
        return {row.id: row.key for row in await connection.execute(select(skill.c.id, skill.c.key))}
    return await cache.ID_MAPS.get("skill_keys", load)


async def _tip_keys(connection: AsyncConnection) -> dict[str, str]:
    async def load():
        tips = await db.table("tips_library")
        return {str(row.id): row.key for row in await connection.execute(select(tips.c.id, tips.c.key))}
    return await cache.ID_MAPS.get("tip_keys", load)


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
            accepted_approaches=list(row.accepted_approaches or []),
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


async def load_questions(connection: AsyncConnection, *, ids: list[uuid.UUID] | None = None,
                         allow_in_review: bool = False) -> list[LoadedQuestion]:
    """Every servable, enriched question (or the given ids) in four round trips, whatever the count."""
    question, translation, link = (await db.table("question"), await db.table("question_translation"),
                                   await db.table("question_skill"))
    condition = [question.c.status.in_(_allowed_statuses(allow_in_review))]
    if ids is not None:
        condition.append(question.c.id.in_(ids))
    rows = (await connection.execute(select(question).where(*condition).order_by(question.c.difficulty, question.c.key))).all()
    if not rows:
        return []
    found = [row.id for row in rows]
    translations: dict[uuid.UUID, list] = {}
    for t in (await connection.execute(select(translation).where(translation.c.question_id.in_(found))
                                       .order_by(translation.c.language))).all():
        translations.setdefault(t.question_id, []).append(t)
    links: dict[uuid.UUID, list] = {}
    for lk in (await connection.execute(select(link).where(link.c.question_id.in_(found))
                                        .order_by(link.c.is_primary.desc(), link.c.weight.desc()))).all():
        links.setdefault(lk.question_id, []).append(lk)
    skill_keys, tip_keys = await _skill_keys(connection), await _tip_keys(connection)
    out = []
    for row in rows:
        if row.id not in translations or not any(bool(lk.is_primary) for lk in links.get(row.id, [])):
            continue                                 # not enriched yet: the engine cannot run it
        out.append(LoadedQuestion(id=row.id, question=_bank_question(row, translations[row.id], links[row.id],
                                                                     skill_keys, tip_keys), version=row.version))
    return out


async def load_question(connection: AsyncConnection, *, key: str | None = None, question_id: uuid.UUID | None = None,
                        allow_in_review: bool = False) -> LoadedQuestion | None:
    """The full engine object for one question, or None when it does not exist or may not be served."""
    if question_id is None:
        question = await db.table("question")
        question_id = (await connection.execute(select(question.c.id).where(question.c.key == key))).scalar_one_or_none()
        if question_id is None:
            return None

    async def load():
        loaded = await load_questions(connection, ids=[question_id], allow_in_review=allow_in_review)
        return loaded[0] if loaded else None
    return await cache.QUESTIONS.get((question_id, allow_in_review), load)


def summary(loaded: LoadedQuestion, language: str) -> QuestionSummary:
    q = loaded.question
    text_language = language if language in q.translations else "en" if "en" in q.translations else next(iter(q.translations))
    text = q.translations[text_language]
    return QuestionSummary(
        id=str(loaded.id), key=q.key, title=text.title or (q.assets.get("titles") or {}).get("en", q.key),
        subject=q.subject, format=q.format, difficulty=q.difficulty, estimated_minutes=q.estimated_minutes,
        practice_modes=list(q.practice_modes), language=text_language, languages=q.languages_ready(), status=q.status,
        hint_count=len(text.hints), has_check=q.deterministic_check is not None,
        reviewed=q.status in ("published", "trial"),   # publishing requires reviewed_by and a permitted reuse status
        trial=q.status == "trial")


def detail(loaded: LoadedQuestion, language: str) -> QuestionDetail:
    base = summary(loaded, language)
    q = loaded.question
    text = q.translations[base.language]
    return QuestionDetail(
        **base.model_dump(), prompt=q.prompt_with_code(base.language), requirements="",  # Internal grading guidance may disclose the solution; never send it to candidates.
        choices=list(text.choices) if text.choices else None, starter_code=q.assets.get("starter_code"),
        code_language=q.assets.get("code_language"))


async def list_questions(connection: AsyncConnection, *, language: str, allow_in_review: bool = False,
                         subject: str | None = None) -> list[QuestionSummary]:
    """Every servable, enriched question as a safe summary."""
    loaded = await load_questions(connection, allow_in_review=allow_in_review)
    return [summary(q, language) for q in loaded if subject is None or q.question.subject == subject]
