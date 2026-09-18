"""Append-only records of what happened: evaluation metrics, model usage, delivered tips.

Nothing here is ever updated. The engine emits dictionaries; this module maps their keys
to columns, resolves catalog keys to ids, and drops what the table has no column for.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db
from app.repo import cache

# engine metric keys that are not columns of evaluation_metrics (they live on the submission)
NOT_COLUMNS = {"band", "check_passed", "submission_revision", "subject_key", "skill_key"}


def _same_columns(rows: list[dict]) -> list[dict]:
    """A multi-row INSERT needs every row to name the same columns; absent ones become NULL.
    (Plain None is right here: none of these columns is JSON.)"""
    columns = sorted({key for row in rows for key in row})
    return [{column: row.get(column) for column in columns} for row in rows]


async def _ids(connection: AsyncConnection, table_name: str) -> dict[str, uuid.UUID]:
    async def load():
        table = await db.table(table_name)
        return {row.key: row.id for row in await connection.execute(select(table.c.id, table.c.key))}
    return await cache.ID_MAPS.get(f"{table_name}_ids", load)


async def record_metrics(connection: AsyncConnection, *, user_id: uuid.UUID, attempt_id: uuid.UUID,
                         metrics: list[dict], seniority: str | None = None) -> int:
    table = await db.table("evaluation_metrics")
    skill_ids = await _ids(connection, "skill")
    columns = set(table.c.keys())
    rows = []
    for metric in metrics:
        row = {k: v for k, v in metric.items() if k in columns and k not in NOT_COLUMNS}
        row.update({
            "user_id": user_id, "attempt_id": attempt_id, "subject_id": skill_ids[metric["subject_key"]],
            "skill_id": skill_ids[metric["skill_key"]], "seniority": seniority,
            "subject_switch": False, "hint_requested_by_user": bool(metric.get("hint_level", 0)) and not metric.get("decision_action"),
            "eval_flags": list(metric.get("eval_flags") or []),
        })
        if metric.get("skill_next"):
            row["skill_next_id"] = skill_ids.get(metric["skill_next"])
        rows.append(row)
    if rows:
        await connection.execute(insert(table), _same_columns(rows))                     # one statement
    return len(rows)


async def record_usage(connection: AsyncConnection, *, user_id: uuid.UUID, attempt_id: uuid.UUID,
                       usage_rows: list[dict]) -> int:
    table = await db.table("usage_event")
    if usage_rows:
        await connection.execute(insert(table), _same_columns([{"user_id": user_id, "attempt_id": attempt_id, **row}
                                                               for row in usage_rows]))
    return len(usage_rows)


async def record_tip(connection: AsyncConnection, *, attempt_id: uuid.UUID, tip_key: str, skill_key: str | None,
                     text: str, timing: str = "post_session") -> uuid.UUID | None:
    delivered = await db.table("delivered_tip")
    tip_id = (await _ids(connection, "tips_library")).get(tip_key)
    if tip_id is None:
        return None
    skill_ids = await _ids(connection, "skill")
    result = await connection.execute(
        insert(delivered).values(attempt_id=attempt_id, tip_id=tip_id, skill_id=skill_ids.get(skill_key) if skill_key else None,
                                 rendered_text=text, timing=timing, was_requested=False, delivered_at=datetime.now(UTC))
        .returning(delivered.c.id))
    return result.scalar_one()
