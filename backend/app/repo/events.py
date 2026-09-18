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

# engine metric keys that are not columns of evaluation_metrics (they live on the submission)
NOT_COLUMNS = {"band", "check_passed", "submission_revision", "subject_key", "skill_key"}


async def _ids(connection: AsyncConnection, table_name: str) -> dict[str, uuid.UUID]:
    table = await db.table(table_name)
    return {row.key: row.id for row in await connection.execute(select(table.c.id, table.c.key))}


async def record_metrics(connection: AsyncConnection, *, user_id: uuid.UUID, attempt_id: uuid.UUID,
                         metrics: list[dict], seniority: str | None = None) -> int:
    table = await db.table("evaluation_metrics")
    skill_ids = await _ids(connection, "skill")
    columns = set(table.c.keys())
    written = 0
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
        await connection.execute(insert(table).values(**row))
        written += 1
    return written


async def record_usage(connection: AsyncConnection, *, user_id: uuid.UUID, attempt_id: uuid.UUID,
                       usage_rows: list[dict]) -> int:
    table = await db.table("usage_event")
    for row in usage_rows:
        await connection.execute(insert(table).values(user_id=user_id, attempt_id=attempt_id, **row))
    return len(usage_rows)


async def record_tip(connection: AsyncConnection, *, attempt_id: uuid.UUID, tip_key: str, skill_key: str | None,
                     text: str, timing: str = "post_session") -> uuid.UUID | None:
    tips = await db.table("tips_library")
    delivered = await db.table("delivered_tip")
    tip_id = (await connection.execute(select(tips.c.id).where(tips.c.key == tip_key))).scalar_one_or_none()
    if tip_id is None:
        return None
    skill_ids = await _ids(connection, "skill")
    result = await connection.execute(
        insert(delivered).values(attempt_id=attempt_id, tip_id=tip_id, skill_id=skill_ids.get(skill_key) if skill_key else None,
                                 rendered_text=text, timing=timing, was_requested=False, delivered_at=datetime.now(UTC))
        .returning(delivered.c.id))
    return result.scalar_one()
