"""The coin ledger: one row per gift, earn, spend, stake, payout or refund; the balance is the sum.

Backend-only writes. A row carries a `reference` that is unique per user ("answer:<attempt>:<revision>", "gift",
"duel:<id>:stake"), so a replayed evaluation or a retried webhook never pays twice. Until the migration is applied
the table is absent: balances read 0 and the writer refuses with a clear error (the pattern of sightings and billing).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import Integer, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db

TABLE = "coin_ledger"
KINDS = ("gift", "earn", "spend", "stake", "payout", "refund", "forfeit")


class CoinsUnavailable(Exception):
    """The ledger table does not exist yet (migration pending)."""


@dataclass
class Movement:
    delta: int
    kind: str
    reference: str | None
    item: str | None
    duel_id: uuid.UUID | None
    meta: dict
    created_at: datetime


async def available() -> bool:
    return await db.has_table(TABLE)


async def balance(connection: AsyncConnection, user_id: uuid.UUID) -> int:
    if not await available():
        return 0
    table = await db.table(TABLE)
    value = (await connection.execute(select(func.coalesce(func.sum(table.c.delta), 0)).where(table.c.user_id == user_id))).scalar()
    return int(value or 0)


async def movements(connection: AsyncConnection, user_id: uuid.UUID, *, limit: int = 20) -> list[Movement]:
    if not await available():
        return []
    table = await db.table(TABLE)
    rows = (await connection.execute(select(table).where(table.c.user_id == user_id)
                                     .order_by(table.c.created_at.desc()).limit(limit))).all()
    return [Movement(delta=int(r.delta), kind=r.kind, reference=r.reference, item=r.item, duel_id=r.duel_id,
                     meta=dict(r.meta or {}), created_at=r.created_at) for r in rows]


async def add(connection: AsyncConnection, *, user_id: uuid.UUID, delta: int, kind: str, reference: str | None,
              item: str | None = None, duel_id: uuid.UUID | None = None, meta: dict | None = None) -> bool:
    """Append one movement. False when the same reference was written before (idempotent)."""
    if not await available():
        raise CoinsUnavailable("coins are not enabled on this database yet")
    table = await db.table(TABLE)
    statement = insert(table).values(id=uuid.uuid4(), user_id=user_id, delta=delta, kind=kind, reference=reference,
                                     item=item, duel_id=duel_id, meta=meta or {}, created_at=datetime.now(UTC))
    if reference is not None:
        statement = statement.on_conflict_do_nothing(index_elements=[table.c.user_id, table.c.reference])
    result = await connection.execute(statement.returning(table.c.id))
    return result.scalar_one_or_none() is not None


async def sum_since(connection: AsyncConnection, user_id: uuid.UUID, *, kinds: tuple[str, ...], since: datetime,
                    meta_key: str | None = None) -> int:
    """The sum of `delta` (or of a numeric meta field) over today's rows of the given kinds."""
    if not await available():
        return 0
    table = await db.table(TABLE)
    column = table.c.meta[meta_key].astext.cast(Integer) if meta_key else table.c.delta
    value = (await connection.execute(
        select(func.coalesce(func.sum(column), 0)).where(table.c.user_id == user_id, table.c.kind.in_(kinds),
                                                         table.c.created_at >= since))).scalar()
    return int(value or 0)


def start_of_today() -> datetime:
    now = datetime.now(UTC)
    return now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
