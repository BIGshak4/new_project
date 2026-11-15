"""One main question feedback per attempt, shared across the bank and daily game."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.api.errors import ApiError


def feedback_month(now: datetime | None = None) -> date:
    israel = ZoneInfo("Asia/Jerusalem")
    today = datetime.now(israel) if now is None else now.astimezone(israel)
    return today.date().replace(day=1)


async def monthly_feedback_remaining(tx, user_id, limit: int) -> int:
    return max(0, limit - await tx.feedback_uses(user_id, feedback_month()))


async def reserve_monthly_feedback(tx, user_id, scope_id, limit: int) -> None:
    await tx.lock_usage(user_id, "monthly_feedback")
    if await tx.has_feedback_use(user_id, scope_id):
        return
    month = feedback_month()
    if await tx.feedback_uses(user_id, month) >= limit:
        raise ApiError("monthly_feedback_limit", "The monthly feedback allowance has been used.")
    await tx.add_feedback_use(user_id, scope_id, month)


async def release_monthly_feedback(tx, user_id, scope_id) -> None:
    await tx.lock_usage(user_id, "monthly_feedback")
    await tx.delete_feedback_use(user_id, scope_id)
