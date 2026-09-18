"""Async database access.

The schema is owned by supabase/migrations/. Rather than hand-maintaining 30 ORM
classes that can drift from it, tables are reflected from the live database once
at startup, so the Python side always matches what the migrations created.

The backend connects as the database owner (service role), which bypasses RLS and
is the only writer for content, sessions, attempts and evaluation tables.
"""

from __future__ import annotations

from sqlalchemy import MetaData, Table, null
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import get_settings

_engine: AsyncEngine | None = None
_metadata: MetaData | None = None


def normalize_url(url: str) -> str:
    """Accept the string Supabase shows (postgresql://...) and select the asyncpg driver."""
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix):]
    return url


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        url = get_settings().database_url
        if not url:
            raise RuntimeError("DATABASE_URL is not set. Copy backend/.env.example to backend/.env and fill it in.")
        # statement_cache_size=0 keeps asyncpg compatible with Supabase's transaction pooler
        _engine = create_async_engine(normalize_url(url), pool_pre_ping=True, pool_size=5, max_overflow=5,
                                      connect_args={"statement_cache_size": 0})
    return _engine


async def get_metadata() -> MetaData:
    global _metadata
    if _metadata is None:
        metadata = MetaData(schema="public")
        async with get_engine().connect() as connection:
            await connection.run_sync(metadata.reflect)
        _metadata = metadata
    return _metadata


async def table(name: str) -> Table:
    metadata = await get_metadata()
    return metadata.tables[f"public.{name}"]


async def dispose() -> None:
    global _engine, _metadata
    if _engine is not None:
        await _engine.dispose()
    _engine, _metadata = None, None


def sql_values(values: dict) -> dict:
    """Column values for an INSERT/UPDATE with Python None as SQL NULL.

    SQLAlchemy serializes None for a JSON column as the JSON value null, which is not SQL NULL:
    `col is null` is false for it and every `jsonb_typeof(col) = 'object'` check fails. Every
    writer goes through this so the rule cannot be forgotten twice.
    """
    return {column: (null() if value is None else value) for column, value in values.items()}
