"""Security regressions: authenticated requests must not multiply bounded model work.

All state and model replies are local fixtures. No production calls or real accounts.
"""
from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace

import pytest

from app.api.errors import ApiError
from app.engine.catalog import load_catalog
from app.engine.providers import ScriptedProvider
from app.repo import cache
from app.services import memory_store
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_practice_hardening import GOOD, SEEDS


@pytest.fixture(scope="module")
def security_catalog():
    return load_catalog(SEEDS)


@pytest.mark.parametrize("kind", ["practice", "interview"])
async def test_daily_allowance_is_atomic_across_service_instances(security_catalog, monkeypatch, kind):
    """Force a database-style yield after COUNT; independent workers share the allowance."""
    store = InMemoryStore(security_catalog)
    method_name = "started_today" if kind == "practice" else "sessions_started_today"
    original = getattr(memory_store._MemoryTx, method_name)

    async def read_then_yield(self, user_id, **kwargs):
        count = await original(self, user_id, **kwargs)
        await asyncio.sleep(0)
        return count

    monkeypatch.setattr(memory_store._MemoryTx, method_name, read_then_yield)
    user_id = uuid.uuid4()
    provider = ScriptedProvider([])  # starting never calls a model
    if kind == "practice":
        services = [PracticeService(store, security_catalog, provider, ServiceConfig(daily_attempt_limit=1))
                    for _ in range(4)]
        starts = [service.start(user_id, question_key="example-sensor-majority") for service in services]
    else:
        services = [InterviewService(store, security_catalog, provider,
                                     InterviewConfig(reviewed_only=False, daily_limit=1)) for _ in range(4)]
        starts = [service.start(user_id, duration_min=20) for service in services]
    results = await asyncio.gather(*starts, return_exceptions=True)
    accepted = [result for result in results if not isinstance(result, BaseException)]
    assert len(accepted) == 1
    denied = [result for result in results if isinstance(result, ApiError)]
    assert len(denied) == 3 and all(error.code == "usage_limit" for error in denied)
    assert len(store.attempts if kind == "practice" else store.sessions) == 1
    assert not provider.requests


async def test_same_key_in_flight_interview_replay_preserves_answer_and_calls_model_once(security_catalog):
    store = InMemoryStore(security_catalog)
    entered, finish = asyncio.Event(), asyncio.Event()
    evaluator_calls = 0

    async def respond(request):
        nonlocal evaluator_calls
        if request.role == "evaluator":
            evaluator_calls += 1
            if evaluator_calls == 1:
                entered.set()
                await finish.wait()
            return GOOD
        return "unused"

    provider = ScriptedProvider(respond)
    first, second = [InterviewService(store, security_catalog, provider, InterviewConfig(reviewed_only=False))
                     for _ in range(2)]
    user_id = uuid.uuid4()
    view = await first.start(user_id, duration_min=20)
    session_id = uuid.UUID(view.id)
    evaluating = asyncio.create_task(first.answer(user_id, session_id, 0, "original answer", idempotency_key="same"))
    await asyncio.wait_for(entered.wait(), 3)
    try:
        replay, recovered = await asyncio.wait_for(
            second.answer(user_id, session_id, 0, "replacement payload", idempotency_key="same"), 3)
        assert evaluator_calls == 1
        assert replay.status == "evaluating" and replay.answer == "original answer"
        assert recovered.current_turn.answer == "original answer"
    finally:
        finish.set()
        await asyncio.gather(evaluating, return_exceptions=True)
    assert len([event for event in store.usage if event.get("session_id") == session_id]) <= 1


async def test_unknown_interview_ids_do_not_accumulate_permanent_locks(security_catalog):
    store = InMemoryStore(security_catalog)
    service = InterviewService(store, security_catalog, ScriptedProvider([]))
    user_id = uuid.uuid4()
    for _ in range(100):
        with pytest.raises(ApiError) as error:
            await service.hint(user_id, uuid.uuid4())
        assert error.value.code == "not_found"
    assert len(service._locks) == 0


async def test_question_style_negative_cache_churn_does_not_retain_expired_ids(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(cache, "time", SimpleNamespace(monotonic=lambda: now[0]))
    bounded = cache.TTLCache(seconds=1)

    async def missing_question():
        return None

    for _ in range(100):
        await bounded.get(uuid.uuid4(), missing_question)
        now[0] += 2
    # Previously all 100 expired misses stayed in this process-global dictionary.
    assert len(bounded._entries) <= 1


async def test_fresh_missing_ids_are_bounded_without_evicting_recently_used_results():
    bounded = cache.TTLCache(seconds=3600, max_entries=4)

    async def found():
        return "published question"

    async def missing():
        return None

    await bounded.get("real-question", found)
    for _ in range(50):
        assert await bounded.get("real-question", found) == "published question"
        await bounded.get(uuid.uuid4(), missing)
    assert len(bounded._entries) == 4
    assert bounded.peek("real-question") == "published question"
