"""One user's monthly model budget (Shaked, 2026-11-14: "i want it to cost us no more than 10 - 15 shekels so set
the amount").

Every model call is recorded with its real cost in `usage_event`. At the door of the two things that spend money, a
new practice attempt and a new mock interview, the user's spend since the first of the month is compared with the
budget; at or above it, nothing new opens until the month turns. What is already open is finished normally, so the
most a user can pass the budget by is the attempt or the interview in hand. The daily limits stay as they are: they
bound a day, this bounds the bill.
"""

from __future__ import annotations

import logging
import uuid

from app.api.errors import ApiError
from app.repo.events import month_start

log = logging.getLogger("app.budget")


async def monthly_budget_left(tx, user_id: uuid.UUID, budget_usd: float) -> None:
    """Refuse (429 usage_limit) when this user's model calls this month have reached the budget; 0 = no budget.

    The read sits in a savepoint and a failure of it opens the door: a budget that cannot be read must not be the
    reason nobody can practise (the daily limits still hold)."""
    if budget_usd <= 0:
        return
    try:
        async with tx.savepoint():
            spent = await tx.model_cost_since(user_id, month_start())
    except Exception:                                       # noqa: BLE001 - logged; the attempt opens
        log.exception("the monthly budget could not be read for %s; nothing is refused", user_id)
        return
    if spent >= budget_usd:
        raise ApiError("usage_limit", "you have reached this month's practice allowance; it starts again on the 1st",
                       headers={"Retry-After": "86400"})
