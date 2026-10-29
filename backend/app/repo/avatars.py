"""Backend-owned cosmetic selection and entitlements; no browser writes."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app import db

TABLE = "game_avatar"


async def available():
    if not await db.has_table(TABLE):
        return False
    return "onboarding_completed" in (await db.table(TABLE)).c


async def load(connection, user_id):
    if not await available():
        return None
    table = await db.table(TABLE)
    row = (await connection.execute(select(table).where(table.c.user_id == user_id))).mappings().first()
    return dict(row) if row else None


async def load_many(connection, user_ids):
    if not await available() or not user_ids:
        return {}
    table = await db.table(TABLE)
    rows = (await connection.execute(select(table).where(table.c.user_id.in_(user_ids)))).mappings().all()
    return {str(row["user_id"]): dict(row) for row in rows}


async def save(connection, user_id, avatar, owned_skins, onboarding_completed=None):
    table = await db.table(TABLE)
    values = {"user_id": user_id, **avatar, "owned_skins": list(owned_skins)}
    if onboarding_completed is not None:
        values["onboarding_completed"] = onboarding_completed
    statement = insert(table).values(**values)
    await connection.execute(statement.on_conflict_do_update(index_elements=[table.c.user_id],
                             set_={k: v for k, v in values.items() if k != "user_id"}))
