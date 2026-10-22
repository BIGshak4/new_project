"""Races on coins and duels (verification, 2026-10-22): two answers landing together, two reads settling an overdue
duel together, two buys with coins for one, two awards for one answer. The in-memory store serialises per
(user, scope) and per duel exactly where the database takes its advisory lock, so the money moves once."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.api.errors import ApiError
from app.engine.catalog import load_catalog
from app.engine.providers import ScriptedProvider
from app.services.coins import CoinsService, load_rules
from app.services.duels import DuelService, load_quiz
from app.services.memory_store import InMemoryStore
from tests.test_practice_hardening import SEEDS

A, B = uuid.uuid4(), uuid.uuid4()
RULES = load_rules(SEEDS / "coins.json")
QUIZ = load_quiz(SEEDS / "duel_quiz.json")


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


class Clock:
    def __init__(self):
        self.now = datetime(2026, 10, 22, 9, 0, tzinfo=UTC)

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)


def services(catalog):
    store = InMemoryStore(catalog)
    coins = CoinsService(store, RULES)
    svc = DuelService(store, catalog, ScriptedProvider(lambda r: "unused"), coins, reviewed_only=False, quiz=QUIZ,
                      approved_only=False)
    svc.clock = Clock()
    return svc, coins, store


def payouts(store, duel_id):
    return [r for r in store.coin_ledger if r["kind"] in ("payout", "refund") and r["duel_id"] == duel_id]


async def gather_errors(*aws):
    return await asyncio.gather(*aws, return_exceptions=True)


class TestDuelRaces:
    async def test_the_last_two_answers_land_together_and_pay_once(self, catalog):
        svc, coins, store = services(catalog)
        duel = await svc.accept(B, (await svc.create(A, language="he")).code)
        corrects = [svc.quiz[i["key"]].correct for i in duel.items]
        for i, c in enumerate(corrects[:-1]):
            svc.clock.advance(2)
            await svc.answer(A, duel.id, choice=c, item=i)
            await svc.answer(B, duel.id, choice=(c + 1) % 4, item=i)
        svc.clock.advance(2)
        results = await gather_errors(svc.answer(A, duel.id, choice=corrects[-1], item=4),
                                      svc.answer(B, duel.id, choice=corrects[-1], item=4))
        assert not [r for r in results if isinstance(r, Exception)], results
        final = await svc.get(A, duel.id)
        assert final.status == "settled" and final.winner_id == A
        assert len(payouts(store, duel.id)) == 1
        assert (await coins.wallet(A)).balance == 55 and (await coins.wallet(B)).balance == 45

    async def test_both_players_read_an_overdue_duel_together(self, catalog):
        svc, coins, store = services(catalog)
        duel = await svc.accept(B, (await svc.create(A, language="he")).code)
        svc.clock.advance(3)
        await svc.answer(A, duel.id, choice=svc.quiz[duel.items[0]["key"]].correct, item=0)
        svc.clock.advance(6 * 60)
        results = await gather_errors(svc.get(A, duel.id), svc.get(B, duel.id), svc.list(A), svc.list(B))
        assert not [r for r in results if isinstance(r, Exception)], results
        final = await svc.get(B, duel.id)
        assert final.outcome == "forfeit_opponent" and len(payouts(store, duel.id)) == 1
        assert (await coins.wallet(A)).balance == 55

    async def test_two_accepts_of_one_invite(self, catalog):
        svc, coins, store = services(catalog)
        c = uuid.uuid4()
        invite = await svc.create(A, language="he")
        results = await gather_errors(svc.accept(B, invite.code), svc.accept(c, invite.code))
        errors = [r for r in results if isinstance(r, ApiError)]
        assert len(errors) == 1 and errors[0].code == "conflict"
        stakes = [r for r in store.coin_ledger if r["kind"] == "stake" and r["duel_id"] == invite.id]
        assert len(stakes) == 2                                     # the challenger's and exactly one opponent's

    async def test_cancel_and_accept_together(self, catalog):
        svc, coins, store = services(catalog)
        invite = await svc.create(A, language="he")
        results = await gather_errors(svc.cancel(A, invite.id), svc.accept(B, invite.code))
        errors = [r for r in results if isinstance(r, ApiError)]
        assert len(errors) == 1 and errors[0].code == "conflict"
        final = await svc.get(A, invite.id)
        a_rows = [r for r in store.coin_ledger if r["user_id"] == A and r["duel_id"] == invite.id]
        if final.status == "cancelled":
            assert [r["kind"] for r in a_rows] == ["stake", "refund"] and (await coins.wallet(A)).balance == 50
        else:
            assert final.status == "active" and [r["kind"] for r in a_rows] == ["stake"]


class TestCoinRaces:
    async def test_two_buys_with_coins_for_one(self, catalog):
        svc, coins, store = services(catalog)
        async with store.transaction() as tx:
            await tx.coin_add(user_id=A, delta=60, kind="earn", reference="seed")   # 110 with the gift: one purchase
        results = await gather_errors(coins.buy(A, "extra_questions_10"), coins.buy(A, "extra_questions_10"))
        errors = [r for r in results if isinstance(r, ApiError)]
        assert len(errors) == 1 and errors[0].status == 402
        assert (await coins.wallet(A)).balance == 10 and await coins.extra_questions_today(A) == 10

    async def test_two_awards_for_one_answer(self, catalog):
        svc, coins, store = services(catalog)
        attempt = uuid.uuid4()

        async def award():
            async with store.transaction() as tx:
                return await coins.award_for_answer(tx, user_id=A, attempt_id=attempt, revision=1, band="STRONG", difficulty=2,
                                                    hints_seen=0, reference_seen=False, related=True, turn=0)
        results = await gather_errors(award(), award())
        assert sorted(r for r in results if not isinstance(r, Exception)) == [0, 10]
        assert (await coins.wallet(A)).balance == 60

    async def test_the_gift_under_two_first_reads(self, catalog):
        svc, coins, store = services(catalog)
        other = CoinsService(store, RULES)
        results = await gather_errors(coins.wallet(A), other.wallet(A), coins.wallet(A))
        assert all(w.balance == 50 for w in results if not isinstance(w, Exception))
        assert sum(1 for r in store.coin_ledger if r["user_id"] == A and r["kind"] == "gift") == 1
