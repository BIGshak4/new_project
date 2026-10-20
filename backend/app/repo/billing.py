"""Paid access: one subscription row per user, one row per Stripe event we have handled.

Backend-only writes (the Stripe webhook and the checkout flow); the browser may read its own subscription row.
Until the migration is applied the tables are absent: readers return "free", the writer refuses with a clear error
(the same pattern as company sightings).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db

SUBSCRIPTIONS = "billing_subscription"
EVENTS = "billing_event"
STATUSES = ("free", "active", "trialing", "past_due", "canceled", "expired")


class BillingUnavailable(Exception):
    """The billing tables do not exist yet (migration pending)."""


@dataclass
class Subscription:
    user_id: uuid.UUID
    status: str = "free"                     # free | active | trialing | past_due | canceled | expired
    plan: str | None = None                  # a key from seeds/billing_plans.json
    customer_id: str | None = None           # Stripe customer
    subscription_id: str | None = None       # Stripe subscription (None for a package)
    period_end: datetime | None = None       # paid through; None = open-ended while active
    cancel_at_period_end: bool = False
    updated_at: datetime | None = None

    def entitled(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(UTC)
        if self.status not in ("active", "trialing"):
            return False
        return self.period_end is None or self.period_end > now

    def as_row(self) -> dict:
        return {"user_id": self.user_id, "status": self.status, "plan": self.plan, "customer_id": self.customer_id,
                "subscription_id": self.subscription_id, "period_end": self.period_end,
                "cancel_at_period_end": self.cancel_at_period_end, "updated_at": self.updated_at or datetime.now(UTC)}


async def available() -> bool:
    return await db.has_table(SUBSCRIPTIONS) and await db.has_table(EVENTS)


def _from_row(row) -> Subscription:
    return Subscription(user_id=row.user_id, status=row.status, plan=row.plan, customer_id=row.customer_id,
                        subscription_id=row.subscription_id, period_end=row.period_end,
                        cancel_at_period_end=bool(row.cancel_at_period_end), updated_at=row.updated_at)


async def load(connection: AsyncConnection, user_id: uuid.UUID) -> Subscription:
    if not await available():
        return Subscription(user_id=user_id)
    table = await db.table(SUBSCRIPTIONS)
    row = (await connection.execute(select(table).where(table.c.user_id == user_id))).first()
    return _from_row(row) if row is not None else Subscription(user_id=user_id)


async def by_customer(connection: AsyncConnection, customer_id: str) -> Subscription | None:
    if not await available():
        return None
    table = await db.table(SUBSCRIPTIONS)
    row = (await connection.execute(select(table).where(table.c.customer_id == customer_id))).first()
    return _from_row(row) if row is not None else None


async def save(connection: AsyncConnection, subscription: Subscription) -> None:
    if not await available():
        raise BillingUnavailable("billing is not enabled on this database yet")
    table = await db.table(SUBSCRIPTIONS)
    row = subscription.as_row()
    statement = insert(table).values(**row)
    await connection.execute(statement.on_conflict_do_update(index_elements=[table.c.user_id],
                                                             set_={k: v for k, v in row.items() if k != "user_id"}))


async def record_event(connection: AsyncConnection, *, event_id: str, kind: str, user_id: uuid.UUID | None,
                       summary: dict) -> bool:
    """True when this Stripe event is new; False when it was handled before (Stripe retries deliveries)."""
    if not await available():
        raise BillingUnavailable("billing is not enabled on this database yet")
    table = await db.table(EVENTS)
    result = await connection.execute(
        insert(table).values(id=event_id, kind=kind, user_id=user_id, summary=summary, received_at=datetime.now(UTC))
        .on_conflict_do_nothing(index_elements=[table.c.id]).returning(table.c.id))
    return result.scalar_one_or_none() is not None
