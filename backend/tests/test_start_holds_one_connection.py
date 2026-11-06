"""Found by the HTTP live test on 2026-11-06: `PracticeService.start` read the day's cap (billing plan + coins top-up,
which open their own transactions) while already inside its own transaction. On a store that hands out one
connection at a time that is a deadlock; on the production pool it is a connection held while waiting for another,
which exhausts the pool under load. The cap is read before the transaction opens now; this test pins it with a store
whose transactions are strictly one at a time, like the live RollbackStore."""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager

import pytest

from app.engine.catalog import load_catalog
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_practice_hardening import GOOD, SEEDS, scripted


class OneAtATimeStore(InMemoryStore):
    """A second `transaction()` while one is open waits for it, exactly like tests/livetools.RollbackStore."""

    def __init__(self, catalog):
        super().__init__(catalog)
        self._one_at_a_time = asyncio.Lock()
        self.max_depth = 0
        self._depth = 0

    @asynccontextmanager
    async def transaction(self):
        async with self._one_at_a_time:
            self._depth += 1
            self.max_depth = max(self.max_depth, self._depth)
            try:
                async with super().transaction() as tx:
                    yield tx
            finally:
                self._depth -= 1


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


async def test_start_reads_the_cap_before_it_opens_its_transaction(catalog):
    store = OneAtATimeStore(catalog)
    svc = PracticeService(store, catalog, scripted([GOOD]), ServiceConfig(suggest_reviewed_only=False))
    looked = {"n": 0}

    async def cap_from_billing_and_coins(user_id):
        async with store.transaction():                     # the billing plan and the coins shop each do this
            looked["n"] += 1
            return 30

    svc.daily_limit_for = cap_from_billing_and_coins
    user = uuid.uuid4()
    question = next(iter(catalog.questions.values()))
    view = await asyncio.wait_for(svc.start(user, question_key=question.key, language="en"), timeout=10)
    assert view.id and looked["n"] == 1 and store.max_depth == 1


async def test_the_memory_store_itself_allows_what_production_pools_do(catalog):
    """Nothing in this test guards production: it documents that the plain memory store is re-entrant, so only the
    one-at-a-time store above can catch the pattern."""
    store = InMemoryStore(catalog)
    async with store.transaction(), store.transaction():
        pass
