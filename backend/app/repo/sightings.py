"""Company sightings: "I saw this question at company X".

One row per (question, user, company). The API shows aggregates per question and a company list for
search; it never shows who reported what. Until the migration is applied the table is absent, and every
reader returns empty while the writer refuses with a clear error.
"""

from __future__ import annotations

import re
import unicodedata
import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db

TABLE = "question_sighting"
MAX_NAME = 80
# Latin letters, digits and Hebrew letters (U+05D0..U+05EA, no vowel points); the table constraint in
# supabase/migrations/20260924045708_question_sightings.sql accepts exactly the same alphabet
_SLUG_JUNK = re.compile(r"[^a-z0-9\u05d0-\u05ea]+")


class SightingsUnavailable(Exception):
    """The table does not exist yet (migration pending)."""


def slugify(name: str) -> str:
    """'  Intel Corp. ' -> 'intel-corp'. Hebrew letters are kept (folded to lowercase where that applies)."""
    folded = unicodedata.normalize("NFKC", name).strip().lower()
    return _SLUG_JUNK.sub("-", folded)[:MAX_NAME].strip("-")          # cut first, so a slug never ends in "-"


def clean_name(name: str) -> str:
    return " ".join(name.split())[:MAX_NAME]


async def available() -> bool:
    return await db.has_table(TABLE)


async def add(connection: AsyncConnection, *, question_id: uuid.UUID, user_id: uuid.UUID, company: str) -> str:
    """Record a sighting; returns the company slug. Idempotent per (question, user, company)."""
    if not await available():
        raise SightingsUnavailable("company tags are not enabled on this database yet")
    name, slug = clean_name(company), slugify(company)
    if not name or not slug:
        raise ValueError("a company name is required")
    table = await db.table(TABLE)
    await connection.execute(insert(table).values(question_id=question_id, user_id=user_id, company_name=name,
                                                  company_slug=slug)
                             .on_conflict_do_nothing(index_elements=["question_id", "user_id", "company_slug"]))
    return slug


async def for_questions(connection: AsyncConnection, question_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[dict]]:
    """{question id: [{slug, name, count}], ...} most reported first."""
    if not question_ids or not await available():
        return {}
    table = await db.table(TABLE)
    rows = (await connection.execute(
        select(table.c.question_id, table.c.company_slug, func.min(table.c.company_name).label("name"),
               func.count().label("count"))
        .where(table.c.question_id.in_(question_ids)).group_by(table.c.question_id, table.c.company_slug))).all()
    out: dict[uuid.UUID, list[dict]] = {}
    for r in rows:
        out.setdefault(r.question_id, []).append({"slug": r.company_slug, "name": r.name, "count": int(r.count)})
    for tags in out.values():
        tags.sort(key=lambda t: (-t["count"], t["slug"]))
    return out


async def question_ids_for_company(connection: AsyncConnection, slug: str) -> set[uuid.UUID]:
    if not await available():
        return set()
    table = await db.table(TABLE)
    rows = await connection.execute(select(table.c.question_id).where(table.c.company_slug == slug).distinct())
    return {r.question_id for r in rows}


async def companies(connection: AsyncConnection) -> list[dict]:
    """Every company reported so far: {slug, name, questions, sightings}, most questions first."""
    if not await available():
        return []
    table = await db.table(TABLE)
    rows = (await connection.execute(
        select(table.c.company_slug, func.min(table.c.company_name).label("name"),
               func.count(func.distinct(table.c.question_id)).label("questions"), func.count().label("sightings"))
        .group_by(table.c.company_slug))).all()
    out = [{"slug": r.company_slug, "name": r.name, "questions": int(r.questions), "sightings": int(r.sightings)} for r in rows]
    return sorted(out, key=lambda c: (-c["questions"], c["slug"]))
