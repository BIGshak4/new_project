"""Judged duels at the deadline (verification, 2026-10-22): an answer sent in time but still with the judge when the
clock runs out is not a no-show; a late answer settles the duel and the settlement survives the refusal."""

from __future__ import annotations

import asyncio
import uuid

import pytest

from app.api.errors import ApiError
from app.engine.catalog import load_catalog
from app.engine.providers import LLMRequest, ScriptedProvider
from app.services.coins import CoinsService
from tests.test_duels import RULES, Clock
from tests.test_duels import service as _service
from tests.test_practice_hardening import GOOD, SEEDS

A, B = uuid.uuid4(), uuid.uuid4()


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


class SlowJudge:
    """The evaluator waits until released, like a model call that outlives the clock."""

    def __init__(self):
        self.gate = asyncio.Event()

    def provider(self):
        async def respond(request: LLMRequest):
            if request.role == "evaluator":
                await self.gate.wait()
                return GOOD
            return "unused"
        return ScriptedProvider(respond)


async def test_an_answer_with_the_judge_at_the_deadline_still_counts(catalog):
    judge = SlowJudge()
    svc, store, clock = _service(catalog, judge.provider())
    duel = await svc.accept(B, (await svc.create(A, language="en", mode="judged")).code)
    clock.advance(170)
    task = asyncio.create_task(svc.answer(A, duel.id, "a careful answer sent at 170 s"))
    await asyncio.sleep(0.05)                                  # the answer is saved as "evaluating"
    clock.advance(20)                                          # the deadline passes while the judge works
    seen = await svc.get(B, duel.id)
    assert seen.status == "active"                             # not forfeited: A's answer is in time, with the judge
    with pytest.raises(ApiError) as late:
        await svc.answer(B, duel.id, "too late")
    assert late.value.code == "conflict"
    judge.gate.set()
    settled = await task
    assert settled.status == "settled" and settled.outcome == "forfeit_opponent" and settled.winner_id == A
    assert (await svc.coins.wallet(A)).balance == 55 and (await svc.coins.wallet(B)).balance == 45


async def test_a_late_answer_settles_the_duel_and_the_settlement_is_kept(catalog):
    svc, store, clock = _service(catalog)
    duel = await svc.accept(B, (await svc.create(A, language="en", mode="judged")).code)
    clock.advance(10)
    await svc.answer(A, duel.id, "in time")
    clock.advance(200)
    with pytest.raises(ApiError):
        await svc.answer(B, duel.id, "late")
    fresh = await svc.get(A, duel.id)
    assert fresh.status == "settled" and fresh.outcome == "forfeit_opponent"
    assert sum(1 for r in store.coin_ledger if r["kind"] == "payout" and r["duel_id"] == duel.id) == 1


async def test_the_grace_ends(catalog):
    judge = SlowJudge()
    svc, store, clock = _service(catalog, judge.provider())
    duel = await svc.accept(B, (await svc.create(A, language="en", mode="judged")).code)
    clock.advance(170)
    task = asyncio.create_task(svc.answer(A, duel.id, "sent at 170 s"))
    await asyncio.sleep(0.05)
    clock.advance(20 + 121)                                    # past the deadline and past the grace
    seen = await svc.get(B, duel.id)
    assert seen.status == "settled" and seen.outcome == "no_show"   # the judge never came back in time
    judge.gate.set()
    done = await task
    assert done.status == "settled" and done.outcome == "no_show"   # the late verdict changes nothing
    assert (await svc.coins.wallet(A)).balance == 50 and (await svc.coins.wallet(B)).balance == 50


def test_imports_used():
    assert Clock and RULES and CoinsService
