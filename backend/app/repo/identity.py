"""Identity and friendship data. The caller's UUID always scopes relationship reads and writes."""

import uuid

from sqlalchemy import and_, delete, or_, select, update

from app import db


async def available() -> bool:
    profile = await db.table("user_profile")
    return {"username", "username_key", "friend_code"} <= set(profile.c.keys()) and await db.has_table("friendship")


def _columns(profile):
    return profile.c.id, profile.c.username, profile.c.friend_code


async def load(connection, user_id):
    profile = await db.table("user_profile")
    row = (await connection.execute(select(*_columns(profile)).where(
        profile.c.id == user_id, profile.c.deleted_at.is_(None)))).mappings().first()
    return dict(row) if row else None


async def load_many(connection, user_ids):
    if not user_ids:
        return {}
    profile = await db.table("user_profile")
    rows = (await connection.execute(select(*_columns(profile)).where(
        profile.c.id.in_(user_ids), profile.c.deleted_at.is_(None)))).mappings().all()
    return {str(row["id"]): dict(row) for row in rows}


async def by_code(connection, friend_code):
    profile = await db.table("user_profile")
    row = (await connection.execute(select(*_columns(profile)).where(
        profile.c.friend_code == friend_code, profile.c.deleted_at.is_(None)))).mappings().first()
    return dict(row) if row else None


async def username_taken(connection, key):
    profile = await db.table("user_profile")
    # Names remain reserved after soft deletion; the unique constraint follows the same rule.
    return (await connection.execute(select(profile.c.id).where(profile.c.username_key == key).limit(1))).first() is not None


async def claim(connection, user_id, username):
    profile = await db.table("user_profile")
    row = (await connection.execute(update(profile).where(
        profile.c.id == user_id, profile.c.username.is_(None), profile.c.deleted_at.is_(None))
        .values(username=username).returning(*_columns(profile)))).mappings().first()
    return dict(row) if row else None


async def relationships(connection, user_id):
    table = await db.table("friendship")
    rows = (await connection.execute(select(table).where(or_(table.c.requester_id == user_id,
        table.c.recipient_id == user_id)).order_by(table.c.created_at, table.c.id).limit(500))).mappings().all()
    return [dict(row) for row in rows]


async def relationship(connection, user_id, request_id=None, other_id=None):
    table = await db.table("friendship")
    query = select(table).where(or_(table.c.requester_id == user_id, table.c.recipient_id == user_id))
    if request_id is not None:
        query = query.where(table.c.id == request_id)
    if other_id is not None:
        query = query.where(or_(table.c.requester_id == other_id, table.c.recipient_id == other_id))
    row = (await connection.execute(query)).mappings().first()
    return dict(row) if row else None


async def add_request(connection, requester_id, recipient_id):
    table = await db.table("friendship")
    result = await connection.execute(table.insert().values(id=uuid.uuid4(), requester_id=requester_id,
        recipient_id=recipient_id, status="pending").returning(table))
    return dict(result.mappings().one())


async def accept(connection, user_id, request_id):
    table = await db.table("friendship")
    from sqlalchemy import func
    result = await connection.execute(update(table).where(table.c.id == request_id,
        table.c.recipient_id == user_id, table.c.status == "pending")
        .values(status="accepted", accepted_at=func.now()).returning(table))
    row = result.mappings().first()
    return dict(row) if row else None


async def delete_request(connection, user_id, request_id, incoming):
    table = await db.table("friendship")
    owner = table.c.recipient_id if incoming else table.c.requester_id
    await connection.execute(delete(table).where(table.c.id == request_id, owner == user_id, table.c.status == "pending"))


async def remove(connection, user_id, other_id):
    table = await db.table("friendship")
    await connection.execute(delete(table).where(table.c.status == "accepted", or_(
        and_(table.c.requester_id == user_id, table.c.recipient_id == other_id),
        and_(table.c.requester_id == other_id, table.c.recipient_id == user_id))))
