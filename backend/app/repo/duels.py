"""Duels: two players, one unseen short question, the same judge, five coins each (Shaked, 2026-10-22).

One row per duel. Backend-only writes; the browser reads nothing here (the API shows each player their own view and
hides the opponent's answer until the duel is settled). Until the migration is applied the table is absent: the
duel routes answer 503 and nothing else changes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db

TABLE = "duel"
STATUSES = ("open", "active", "settled", "cancelled")
OUTCOMES = ("challenger", "opponent", "draw", "forfeit_challenger", "forfeit_opponent", "no_show", "cancelled", "expired")


class DuelsUnavailable(Exception):
    """The duel table does not exist yet (migration pending)."""


class StaleDuel(Exception):
    """Another request changed the duel first (optimistic version)."""


@dataclass
class Duel:
    id: uuid.UUID
    code: str                                    # the invite code in the link
    status: str                                  # open | active | settled | cancelled
    challenger_id: uuid.UUID
    opponent_id: uuid.UUID | None
    language: str
    stake: int
    clock_seconds: int
    question_key: str | None = None              # chosen when the opponent accepts: unseen by both
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    accepted_at: datetime | None = None
    deadline: datetime | None = None
    settled_at: datetime | None = None
    outcome: str | None = None
    winner_id: uuid.UUID | None = None
    players: dict = field(default_factory=dict)  # str(user_id) -> {answer, band, submitted_at, summary, flags, model}
    meta: dict = field(default_factory=dict)
    version: int = 0

    def player(self, user_id: uuid.UUID) -> dict:
        return self.players.setdefault(str(user_id), {})

    def is_player(self, user_id: uuid.UUID) -> bool:
        return user_id in (self.challenger_id, self.opponent_id)

    def other(self, user_id: uuid.UUID) -> uuid.UUID | None:
        return self.opponent_id if user_id == self.challenger_id else self.challenger_id

    def as_row(self) -> dict:
        return {"id": self.id, "code": self.code, "status": self.status, "challenger_id": self.challenger_id,
                "opponent_id": self.opponent_id, "language": self.language, "stake": self.stake,
                "clock_seconds": self.clock_seconds, "question_key": self.question_key, "created_at": self.created_at,
                "accepted_at": self.accepted_at, "deadline": self.deadline, "settled_at": self.settled_at,
                "outcome": self.outcome, "winner_id": self.winner_id, "players": self.players, "meta": self.meta,
                "version": self.version}


def _from_row(row) -> Duel:
    return Duel(id=row.id, code=row.code, status=row.status, challenger_id=row.challenger_id, opponent_id=row.opponent_id,
                language=row.language, stake=int(row.stake), clock_seconds=int(row.clock_seconds),
                question_key=row.question_key, created_at=row.created_at, accepted_at=row.accepted_at,
                deadline=row.deadline, settled_at=row.settled_at, outcome=row.outcome, winner_id=row.winner_id,
                players=dict(row.players or {}), meta=dict(row.meta or {}), version=int(row.version or 0))


async def available() -> bool:
    return await db.has_table(TABLE)


async def create(connection: AsyncConnection, duel: Duel) -> None:
    if not await available():
        raise DuelsUnavailable("duels are not enabled on this database yet")
    table = await db.table(TABLE)
    await connection.execute(insert(table).values(**db.sql_values(duel.as_row())))


async def load(connection: AsyncConnection, duel_id: uuid.UUID) -> Duel | None:
    if not await available():
        return None
    table = await db.table(TABLE)
    row = (await connection.execute(select(table).where(table.c.id == duel_id))).first()
    return _from_row(row) if row else None


async def by_code(connection: AsyncConnection, code: str) -> Duel | None:
    if not await available():
        return None
    table = await db.table(TABLE)
    row = (await connection.execute(select(table).where(table.c.code == code))).first()
    return _from_row(row) if row else None


async def save(connection: AsyncConnection, duel: Duel) -> None:
    """Write the duel at `version + 1`; raises StaleDuel when another request wrote first."""
    if not await available():
        raise DuelsUnavailable("duels are not enabled on this database yet")
    table = await db.table(TABLE)
    expected = duel.version
    duel.version = expected + 1
    values = {k: v for k, v in db.sql_values(duel.as_row()).items() if k != "id"}
    result = await connection.execute(update(table).where(table.c.id == duel.id, table.c.version == expected).values(**values))
    if result.rowcount != 1:
        duel.version = expected
        raise StaleDuel(f"duel {duel.id} changed meanwhile")


async def list_for(connection: AsyncConnection, user_id: uuid.UUID, *, limit: int = 20) -> list[Duel]:
    if not await available():
        return []
    table = await db.table(TABLE)
    rows = (await connection.execute(
        select(table).where((table.c.challenger_id == user_id) | (table.c.opponent_id == user_id))
        .order_by(table.c.created_at.desc()).limit(limit))).all()
    return [_from_row(r) for r in rows]


async def last_between(connection: AsyncConnection, a: uuid.UUID, b: uuid.UUID) -> datetime | None:
    """When these two last started a duel together (the cooldown)."""
    if not await available():
        return None
    table = await db.table(TABLE)
    pair = ((table.c.challenger_id == a) & (table.c.opponent_id == b)) | ((table.c.challenger_id == b) & (table.c.opponent_id == a))
    return (await connection.execute(select(func.max(table.c.accepted_at)).where(pair))).scalar()


async def accepted_today(connection: AsyncConnection, user_id: uuid.UUID) -> int:
    if not await available():
        return 0
    table = await db.table(TABLE)
    now = datetime.now(UTC)
    start = now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
    value = (await connection.execute(
        select(func.count()).select_from(table)
        .where((table.c.challenger_id == user_id) | (table.c.opponent_id == user_id), table.c.accepted_at >= start))).scalar()
    return int(value or 0)


async def question_keys_played(connection: AsyncConnection, user_id: uuid.UUID) -> set[str]:
    """Questions this user already met in a duel: never asked again in one."""
    if not await available():
        return set()
    table = await db.table(TABLE)
    rows = (await connection.execute(
        select(table.c.question_key).where((table.c.challenger_id == user_id) | (table.c.opponent_id == user_id),
                                           table.c.question_key.is_not(None)))).all()
    return {r.question_key for r in rows}
