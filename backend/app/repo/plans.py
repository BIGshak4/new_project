"""The user's saved program: one active `learning_plan` with its `plan_item` rows (Data_Models §15).

The Plan Router decides what the week should hold; this module remembers it, so a skipped day is carried
forward instead of forgotten, and a finished attempt or interview ticks the item it fulfilled. The browser may
read these rows through RLS (Harel's app); only the backend writes them.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db
from app.repo.profiles import _skill_ids
from app.repo.questions import _skill_keys
from app.repo.sessions import _versioned_id

ROUTER_VERSION = "plan_router.v1"
OPEN = ("planned", "started")


@dataclass
class PlanItemRow:
    id: uuid.UUID
    day_index: int                        # the day the router planned it for, relative to week_start (never moved)
    mode: str                             # quick | deep | simulation | diagnostic | retention_check
    skills: list[str]
    reason: str
    minutes: int
    status: str = "planned"               # planned | started | done | skipped
    completed_attempt_id: uuid.UUID | None = None
    completed_session_id: uuid.UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class StoredPlan:
    id: uuid.UUID
    user_id: uuid.UUID
    week_start: date
    minutes_per_day: int
    interview_date: date | None
    seniority: str
    generated_at: datetime
    items: list[PlanItemRow] = field(default_factory=list)

    def day_index_of(self, today: date) -> int:
        return (today - self.week_start).days


async def load_active(connection: AsyncConnection, user_id: uuid.UUID) -> StoredPlan | None:
    plans, items = await db.table("learning_plan"), await db.table("plan_item")
    row = (await connection.execute(select(plans).where(plans.c.user_id == user_id, plans.c.is_active.is_(True)))).first()
    if row is None:
        return None
    keys = await _skill_keys(connection)
    rows = (await connection.execute(select(items).where(items.c.plan_id == row.id)
                                     .order_by(items.c.day_index, items.c.created_at))).all()
    return StoredPlan(
        id=row.id, user_id=row.user_id, week_start=row.week_start, minutes_per_day=int(row.minutes_per_day or 30),
        interview_date=row.target_interview_date, seniority=str(row.seniority), generated_at=row.generated_at,
        items=[PlanItemRow(id=r.id, day_index=int(r.day_index), mode=str(r.mode),
                           skills=[keys[s] for s in (r.skill_ids or []) if s in keys], reason=r.reason,
                           minutes=int(r.estimated_minutes or 0), status=str(r.status),
                           completed_attempt_id=r.completed_attempt_id, completed_session_id=r.completed_session_id,
                           created_at=r.created_at) for r in rows])


async def deactivate(connection: AsyncConnection, user_id: uuid.UUID) -> None:
    plans = await db.table("learning_plan")
    await connection.execute(update(plans).where(plans.c.user_id == user_id, plans.c.is_active.is_(True)).values(is_active=False))


async def create(connection: AsyncConnection, *, user_id: uuid.UUID, role_slug: str, seniority: str, week_start: date,
                 minutes_per_day: int, interview_date: date | None, items: list[dict]) -> StoredPlan:
    """Replace the active plan. `items`: {day_index, mode, skills, reason, minutes, created_at?} in the order to keep."""
    await deactivate(connection, user_id)
    plans, table = await db.table("learning_plan"), await db.table("plan_item")
    role_id, _ = await _versioned_id(connection, "role_template", role_slug)
    skill_ids = await _skill_ids(connection)
    now = datetime.now(UTC)
    plan_id = (await connection.execute(insert(plans).values(**db.sql_values({
        "user_id": user_id, "target_role_id": role_id, "seniority": seniority, "target_interview_date": interview_date,
        "week_start": week_start, "minutes_per_day": max(1, min(720, minutes_per_day)), "is_active": True,
        "generated_at": now, "router_version": ROUTER_VERSION})).returning(plans.c.id))).scalar_one()
    stored: list[PlanItemRow] = []
    for item in items:
        created = item.get("created_at") or now
        row = {"plan_id": plan_id, "day_index": int(item["day_index"]), "mode": item["mode"],
               "skill_ids": [skill_ids[k] for k in item["skills"] if k in skill_ids], "reason": item["reason"] or "-",
               "estimated_minutes": max(1, min(120, int(item["minutes"] or 1))), "status": "planned", "created_at": created}
        item_id = (await connection.execute(insert(table).values(**db.sql_values(row)).returning(table.c.id))).scalar_one()
        stored.append(PlanItemRow(id=item_id, day_index=row["day_index"], mode=row["mode"], skills=list(item["skills"]),
                                  reason=row["reason"], minutes=row["estimated_minutes"], created_at=created))
    return StoredPlan(id=plan_id, user_id=user_id, week_start=week_start, minutes_per_day=minutes_per_day,
                      interview_date=interview_date, seniority=seniority, generated_at=now, items=stored)


async def update_item(connection: AsyncConnection, item_id: uuid.UUID, **fields) -> None:
    table = await db.table("plan_item")
    await connection.execute(update(table).where(table.c.id == item_id).values(**db.sql_values(fields)))


async def link_attempt(connection: AsyncConnection, attempt_id: uuid.UUID, item_id: uuid.UUID) -> None:
    attempt = await db.table("attempt")
    await connection.execute(update(attempt).where(attempt.c.id == attempt_id).values(plan_item_id=item_id))


async def attempt_item(connection: AsyncConnection, attempt_id: uuid.UUID) -> uuid.UUID | None:
    attempt = await db.table("attempt")
    return (await connection.execute(select(attempt.c.plan_item_id).where(attempt.c.id == attempt_id))).scalar_one_or_none()
