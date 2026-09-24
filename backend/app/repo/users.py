"""Who may practise, and their profile row.

Pilot access is Harel's allowlist, `jr_members` (keyed by e-mail). `can_manage_tasks` is
his founder flag; the practice API reads it and never grants it. The `user_profile` row is
normally created by the signup trigger; the insert here covers accounts created before it.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db
from app.api.errors import ApiError
from app.auth import AuthenticatedUser


@dataclass(frozen=True)
class Access:
    user_id: uuid.UUID
    email: str | None
    is_member: bool
    can_manage_tasks: bool
    profile_created: bool


async def resolve_access(connection: AsyncConnection, user: AuthenticatedUser) -> Access:
    members, profiles = await db.table("jr_members"), await db.table("user_profile")
    is_member, can_manage = False, False
    if user.email:
        row = (await connection.execute(
            select(members.c.can_manage_tasks).where(func.lower(members.c.email) == user.email.lower()))).first()
        if row is not None:
            is_member, can_manage = True, bool(row.can_manage_tasks)
    try:
        result = await connection.execute(
            insert(profiles).values(id=user.id, display_name=(user.display_name or "")[:120] or None)
            .on_conflict_do_nothing(index_elements=["id"]).returning(profiles.c.id))
        created = result.first() is not None
    except IntegrityError as exc:
        # a token for an account that no longer exists in Auth (deleted, token not yet expired).
        # The caller's transaction is dedicated to this lookup, so it may simply fail.
        raise ApiError("unauthenticated", "this account no longer exists; sign in again") from exc
    return Access(user_id=user.id, email=user.email, is_member=is_member, can_manage_tasks=can_manage,
                  profile_created=created)


# ----------------------------------------------------------------------------- the user's goal

SENIORITIES = ("student", "junior", "mid", "senior", "staff", "principal")      # public.seniority enum


@dataclass
class Goal:
    """What the user is preparing for: the job type, when the interview is, how much time they have per day.

    Stored on `user_profile` without a schema change: `background["job_type"]`, `target_interview_date`,
    `available_minutes_per_day`, `seniority_self_assessed`. Every field is optional; `complete` says whether the
    onboarding questions were answered."""

    job_type: str | None = None
    interview_date: date | None = None
    minutes_per_day: int | None = None
    seniority: str | None = None

    @property
    def complete(self) -> bool:
        return self.job_type is not None and self.minutes_per_day is not None

    def days_to_interview(self, today: date | None = None) -> int | None:
        if self.interview_date is None:
            return None
        return (self.interview_date - (today or date.today())).days


async def load_goal(connection: AsyncConnection, user_id: uuid.UUID) -> Goal:
    profiles = await db.table("user_profile")
    row = (await connection.execute(
        select(profiles.c.background, profiles.c.target_interview_date, profiles.c.available_minutes_per_day,
               profiles.c.seniority_self_assessed).where(profiles.c.id == user_id))).first()
    if row is None:
        return Goal()
    background = row.background if isinstance(row.background, dict) else {}
    job_type = background.get("job_type")
    return Goal(job_type=str(job_type) if job_type else None, interview_date=row.target_interview_date,
                minutes_per_day=int(row.available_minutes_per_day) if row.available_minutes_per_day is not None else None,
                seniority=str(row.seniority_self_assessed) if row.seniority_self_assessed else None)


async def save_goal(connection: AsyncConnection, user_id: uuid.UUID, goal: Goal) -> Goal:
    """Write the goal onto the profile row (which the signup trigger or resolve_access created)."""
    profiles = await db.table("user_profile")
    current = (await connection.execute(select(profiles.c.background).where(profiles.c.id == user_id))).scalar_one_or_none()
    background = dict(current) if isinstance(current, dict) else {}
    if goal.job_type:
        background["job_type"] = goal.job_type
    else:
        background.pop("job_type", None)
    values = {"background": background, "target_interview_date": goal.interview_date,
              "available_minutes_per_day": goal.minutes_per_day}
    if goal.seniority:                       # None keeps the profile's value: the column is also Harel's app's
        values["seniority_self_assessed"] = goal.seniority
    await connection.execute(update(profiles).where(profiles.c.id == user_id).values(**db.sql_values(values)))
    return goal
