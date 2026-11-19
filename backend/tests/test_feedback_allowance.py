import asyncio
import uuid
from datetime import UTC, date, datetime

import pytest

from app.api.errors import ApiError
from app.engine.catalog import load_catalog
from app.engine.providers import LLMError
from app.services.feedback_quota import feedback_month, monthly_feedback_remaining, reserve_monthly_feedback
from tests.test_practice_hardening import GOOD, SEEDS, scripted
from tests.test_practice_service import Q, USER, service


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


async def test_bank_submission_and_daily_attempt_share_the_last_credit(catalog):
    svc, store = service(catalog, scripted([GOOD]), monthly_feedback_limit=1)
    view = await svc.start(USER, question_key=Q)
    attempt_id = uuid.UUID(view.id)
    sub, _ = await svc.submit(USER, attempt_id, "My solution", idempotency_key="first")
    assert sub.status == "done"
    await svc.submit(USER, attempt_id, "My solution", idempotency_key="first")
    async with store.transaction() as tx:
        assert await monthly_feedback_remaining(tx, USER, 1) == 0
        with pytest.raises(ApiError, match="monthly feedback") as error:
            await reserve_monthly_feedback(tx, USER, uuid.uuid4(), 1)
        assert error.value.status == 429
    # Feedback delivered before this feature shipped still counts.
    store.feedback_allowance.clear()
    async with store.transaction() as tx:
        assert await monthly_feedback_remaining(tx, USER, 1) == 0


async def test_provider_failure_refunds_and_retry_cannot_overrun_quota(catalog):
    svc, store = service(catalog, scripted([LLMError("down", retryable=False)]), monthly_feedback_limit=1)
    attempt_id = uuid.UUID((await svc.start(USER, question_key=Q)).id)
    failed, _ = await svc.submit(USER, attempt_id, "My answer", idempotency_key="a")
    assert failed.status == "failed"
    async with store.transaction() as tx:
        assert await monthly_feedback_remaining(tx, USER, 1) == 1
        await reserve_monthly_feedback(tx, USER, uuid.uuid4(), 1)
    with pytest.raises(ApiError) as err:
        await svc.retry(USER, attempt_id)
    assert err.value.code == "monthly_feedback_limit"


async def test_concurrent_allocations_share_last_slot(catalog):
    _, store = service(catalog, scripted([]))
    async def spend():
        async with store.transaction() as tx:
            await reserve_monthly_feedback(tx, USER, uuid.uuid4(), 1)
    results = await asyncio.gather(spend(), spend(), return_exceptions=True)
    assert results.count(None) == 1
    assert any(isinstance(result, ApiError) and result.code == "monthly_feedback_limit" for result in results)


def test_feedback_month_changes_at_midnight_in_israel():
    assert feedback_month(datetime(2026, 6, 30, 20, 59, tzinfo=UTC)) == date(2026, 6, 1)
    assert feedback_month(datetime(2026, 6, 30, 21, 0, tzinfo=UTC)) == date(2026, 7, 1)
