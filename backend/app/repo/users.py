"""Who may practise, and their profile row.

Pilot access is Harel's allowlist, `jr_members` (keyed by e-mail). `can_manage_tasks` is
his founder flag; the practice API reads it and never grants it. The `user_profile` row is
normally created by the signup trigger; the insert here covers accounts created before it.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db
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
            select(members.c.can_manage_tasks).where(members.c.email == user.email.lower()))).first()
        if row is not None:
            is_member, can_manage = True, bool(row.can_manage_tasks)
    result = await connection.execute(
        insert(profiles).values(id=user.id, display_name=(user.display_name or "")[:120] or None)
        .on_conflict_do_nothing(index_elements=["id"]).returning(profiles.c.id))
    created = result.first() is not None
    return Access(user_id=user.id, email=user.email, is_member=is_member, can_manage_tasks=can_manage,
                  profile_created=created)
