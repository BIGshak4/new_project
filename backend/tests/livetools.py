"""Run the real service against the real database with zero residue.

`RollbackStore` is a DbStore whose "transactions" are savepoints on ONE connection whose
outer transaction is rolled back when the test module ends. Commits inside the service
become savepoint releases, so every database rule (unique keys, checks, RLS) applies
exactly as in production, and nothing survives the run.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.services.store import DbStore, DbTx


class RollbackStore(DbStore):
    def __init__(self, connection: AsyncConnection, *, allow_in_review: bool = True):
        super().__init__(None, allow_in_review=allow_in_review)
        self.connection = connection
        # one connection runs one statement at a time: work started in the background (the feedback after the
        # grade) waits for the unit of work in progress instead of interleaving on the same connection
        self._one_at_a_time = asyncio.Lock()

    @asynccontextmanager
    async def transaction(self):
        async with self._one_at_a_time:
            savepoint = await self.connection.begin_nested()
            try:
                yield DbTx(self.connection, allow_in_review=self.allow_in_review)
            except BaseException:
                await savepoint.rollback()
                raise
            else:
                await savepoint.commit()


@asynccontextmanager
async def as_signed_in_user(connection: AsyncConnection, user_id: uuid.UUID, email: str):
    """Run statements the way PostgREST would for this user: role `authenticated` with their JWT claims.
    Everything is inside a savepoint, so the role switch is undone afterwards."""
    savepoint = await connection.begin_nested()
    claims = json.dumps({"sub": str(user_id), "role": "authenticated", "email": email, "aud": "authenticated"})
    try:
        await connection.execute(text("select set_config('request.jwt.claims', :claims, true)"), {"claims": claims})
        await connection.execute(text("set local role authenticated"))
        yield
    finally:
        await savepoint.rollback()
