"""Per-user short-card history. All owner checks also apply when RLS is bypassed by the API role."""
from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import case, delete, func, select
from sqlalchemy.dialects.postgresql import insert

from app import db
from app.api.errors import ApiError
from app.schemas.fundamentals import FundamentalsCompletion


class FundamentalsRepository(Protocol):
    async def list_completed(self, user_id: uuid.UUID) -> list[FundamentalsCompletion]: ...

    async def complete(self, user_id: uuid.UUID, question_key: str,
                       content_revision: str) -> FundamentalsCompletion: ...

    async def remove(self, user_id: uuid.UUID, question_key: str) -> bool: ...


class MemoryFundamentalsRepository:
    """Development/test storage, isolated to a runtime and lost when that process restarts."""

    def __init__(self):
        self.rows: dict[tuple[uuid.UUID, str], FundamentalsCompletion] = {}
        self._lock = asyncio.Lock()

    async def list_completed(self, user_id: uuid.UUID) -> list[FundamentalsCompletion]:
        async with self._lock:
            return sorted((row for (owner, _), row in self.rows.items() if owner == user_id),
                          key=lambda row: row.question_key)

    async def complete(self, user_id: uuid.UUID, question_key: str,
                       content_revision: str) -> FundamentalsCompletion:
        async with self._lock:
            key = (user_id, question_key)
            old = self.rows.get(key)
            if old is not None and old.content_revision == content_revision:
                return old
            row = FundamentalsCompletion(question_key=question_key, content_revision=content_revision,
                                         completed_at=datetime.now(UTC))
            self.rows[key] = row
            return row

    async def remove(self, user_id: uuid.UUID, question_key: str) -> bool:
        async with self._lock:
            return self.rows.pop((user_id, question_key), None) is not None


class DbFundamentalsRepository:
    async def _table(self):
        if not await db.has_table("fundamentals_completion"):
            raise ApiError("temporarily_unavailable", "short-practice history is temporarily unavailable", status=503)
        return await db.table("fundamentals_completion")

    async def list_completed(self, user_id: uuid.UUID) -> list[FundamentalsCompletion]:
        table = await self._table()
        async with db.get_engine().begin() as connection:
            result = await connection.execute(select(table.c.question_key, table.c.content_revision, table.c.completed_at)
                                              .where(table.c.user_id == user_id).order_by(table.c.question_key))
            return [FundamentalsCompletion.model_validate(dict(row._mapping)) for row in result]

    async def complete(self, user_id: uuid.UUID, question_key: str,
                       content_revision: str) -> FundamentalsCompletion:
        table = await self._table()
        statement = insert(table).values(user_id=user_id, question_key=question_key, content_revision=content_revision)
        # Repeated marking of the same revision preserves its original completion time.
        statement = statement.on_conflict_do_update(
            index_elements=[table.c.user_id, table.c.question_key],
            set_={"content_revision": statement.excluded.content_revision,
                  "completed_at": case((table.c.content_revision != statement.excluded.content_revision, func.now()),
                                       else_=table.c.completed_at)},
        ).returning(table.c.question_key, table.c.content_revision, table.c.completed_at)
        async with db.get_engine().begin() as connection:
            row = (await connection.execute(statement)).one()
            return FundamentalsCompletion.model_validate(dict(row._mapping))

    async def remove(self, user_id: uuid.UUID, question_key: str) -> bool:
        table = await self._table()
        async with db.get_engine().begin() as connection:
            result = await connection.execute(delete(table).where(table.c.user_id == user_id,
                                                                  table.c.question_key == question_key)
                                              .returning(table.c.question_key))
            return result.first() is not None
