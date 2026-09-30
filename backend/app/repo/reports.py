"""Question reports: "this question is not clear" (or wrong), with an optional note, from a candidate.

One row per (question, user, reason); pressing again updates the note. The API only ever returns a count; the rows
are read by the review tooling (scripts/question_reports.py). Until the migration is applied the table is absent,
and the writer refuses with a clear error (the API turns that into 503 temporarily_unavailable).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db

TABLE = "question_report"
REASONS = ("unclear", "wrong", "other")
CONTEXTS = ("practice", "interview", "library")
MAX_NOTE = 500


class ReportsUnavailable(Exception):
    """The table does not exist yet (migration pending)."""


def clean_note(note: str | None) -> str | None:
    text = " ".join((note or "").split())[:MAX_NOTE]
    return text or None


async def available() -> bool:
    return await db.has_table(TABLE)


async def add(connection: AsyncConnection, *, question_id: uuid.UUID, user_id: uuid.UUID, reason: str, note: str | None,
              language: str, context: str) -> int:
    """Record (or refresh) a report; returns how many open reports the question has afterwards."""
    if not await available():
        raise ReportsUnavailable("question reports are not enabled on this database yet")
    if reason not in REASONS:
        raise ValueError(f"reason must be one of {', '.join(REASONS)}")
    if context not in CONTEXTS:
        raise ValueError(f"context must be one of {', '.join(CONTEXTS)}")
    if language not in ("he", "en"):
        raise ValueError("language must be he or en")
    table = await db.table(TABLE)
    statement = insert(table).values(question_id=question_id, user_id=user_id, reason=reason, note=clean_note(note),
                                     language=language, context=context)
    statement = statement.on_conflict_do_update(
        index_elements=["question_id", "user_id", "reason"],
        set_={"note": statement.excluded.note, "context": statement.excluded.context, "language": statement.excluded.language,
              "created_at": func.now(), "resolved_at": None, "resolved_by": None})
    await connection.execute(statement)
    return await open_count(connection, question_id)


async def open_count(connection: AsyncConnection, question_id: uuid.UUID) -> int:
    table = await db.table(TABLE)
    return int(await connection.scalar(select(func.count()).select_from(table)
                                       .where(table.c.question_id == question_id, table.c.resolved_at.is_(None))) or 0)


async def counts_for(connection: AsyncConnection, question_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    """{question id: open reports}, for the review report; empty when the table is absent."""
    if not question_ids or not await available():
        return {}
    table = await db.table(TABLE)
    rows = await connection.execute(select(table.c.question_id, func.count()).where(table.c.question_id.in_(question_ids),
                                                                                    table.c.resolved_at.is_(None))
                                    .group_by(table.c.question_id))
    return {row[0]: int(row[1]) for row in rows}


async def open_reports(connection: AsyncConnection) -> list[dict]:
    """Every open report, newest first, for the review script."""
    if not await available():
        return []
    table = await db.table(TABLE)
    rows = await connection.execute(select(table.c.id, table.c.question_id, table.c.user_id, table.c.reason, table.c.note,
                                           table.c.language, table.c.context, table.c.created_at)
                                    .where(table.c.resolved_at.is_(None)).order_by(table.c.created_at.desc()))
    return [dict(row._mapping) for row in rows]


async def resolve(connection: AsyncConnection, report_ids: list[uuid.UUID], *, by: str) -> int:
    if not report_ids or not await available():
        return 0
    table = await db.table(TABLE)
    result = await connection.execute(update(table).where(table.c.id.in_(report_ids), table.c.resolved_at.is_(None))
                                      .values(resolved_at=datetime.now(UTC), resolved_by=by))
    return int(result.rowcount or 0)
