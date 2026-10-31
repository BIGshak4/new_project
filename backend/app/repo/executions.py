"""A durable execution allowance and idempotency ledger. It stores no source or credentials."""

from __future__ import annotations

import asyncio
import json
import time
import uuid

from sqlalchemy import text

from app import db
from app.api.errors import ApiError


class MemoryExecutionLedger:
    def __init__(self, *, daily=60, per_minute=6, concurrent=2):
        self.daily, self.per_minute, self.concurrent = daily, per_minute, concurrent
        self.rows: dict[tuple[str, str, str], dict] = {}
        self.lock = asyncio.Lock()

    async def replay(self, user: str, scope: str, key: str, digest: str):
        async with self.lock:
            old = self.rows.get((user, scope, key))
            return _existing(old, digest)[1] if old else None

    async def reserve(self, user: str, scope: str, key: str, digest: str):
        async with self.lock:
            now = time.time()
            # This store is development-only. Bound both memory and the stale-running window.
            self.rows = {k: r for k, r in self.rows.items() if r["created"] > now - 86400 * 2}
            old = self.rows.get((user, scope, key))
            if old:
                return _existing(old, digest)
            rows = list(self.rows.values())
            _limits(rows, user, now, self.daily, self.per_minute, self.concurrent)
            row = dict(id=str(uuid.uuid4()), user=user, scope=scope, key=key,
                       digest=digest, created=now, result=None)
            self.rows[user, scope, key] = row
            return row["id"], None

    async def finish(self, run_id: str, result: dict):
        async with self.lock:
            for row in self.rows.values():
                if row["id"] == run_id:
                    row["result"] = result
                    return

    async def cached(self, user: str, scope: str, digest: str):
        async with self.lock:
            for row in reversed(list(self.rows.values())):
                if (row["user"] == user and row["scope"] == scope and row["digest"] == digest
                        and row["created"] > time.time() - 3600 and row["result"]
                        and row["result"]["status"] != "unavailable"):
                    return row["result"]
        return None


def _existing(row: dict, digest: str):
    if row["digest"] != digest:
        raise ApiError("conflict", "this execution key was already used for different code")
    if row["result"] is None:
        raise ApiError("conflict", "this execution is running or was interrupted; use a new run key")
    return str(row["id"]), row["result"]


def _limits(rows, user, now, daily, per_minute, concurrent):
    mine = [r for r in rows if r["user"] == user]
    _count_limits(sum(r["created"] > now - 86400 for r in mine),
                  sum(r["created"] > now - 60 for r in mine),
                  sum(r["result"] is None and r["created"] > now - 120 for r in rows),
                  daily, per_minute, concurrent)


def _count_limits(day_used, minute_used, active, daily, per_minute, concurrent):
    if day_used >= daily:
        raise ApiError("usage_limit", "the code execution daily allowance has been reached", headers={"Retry-After": "3600"})
    if minute_used >= per_minute:
        raise ApiError("usage_limit", "please wait before running code again", headers={"Retry-After": "60"})
    if active >= concurrent:
        raise ApiError("usage_limit", "the code runner is busy; please retry shortly", headers={"Retry-After": "10"})


class DbExecutionLedger:
    def __init__(self, *, daily=60, per_minute=6, concurrent=2):
        self.daily, self.per_minute, self.concurrent = daily, per_minute, concurrent

    async def replay(self, user: str, scope: str, key: str, digest: str):
        async with db.get_engine().connect() as conn:
            result = await conn.execute(text("""select id, request_hash as digest, result
                from public.code_execution_runs where user_id=cast(:user as uuid)
                and scope=:scope and idempotency_key=:key"""), dict(user=user, scope=scope, key=key))
            old = result.mappings().one_or_none()
            return _existing(dict(old), digest)[1] if old else None

    async def reserve(self, user: str, scope: str, key: str, digest: str):
        async with db.get_engine().begin() as conn:
            # All API processes share this short lock; no transaction stays open during a VM run.
            await conn.execute(text("select pg_advisory_xact_lock(724018602559)"))
            existing = await conn.execute(text("""select id, request_hash as digest, result
                from public.code_execution_runs where user_id=cast(:user as uuid)
                and scope=:scope and idempotency_key=:key"""), dict(user=user, scope=scope, key=key))
            old = existing.mappings().one_or_none()
            if old:
                return _existing(dict(old), digest)
            # Quotas require three counts, never other learners' result payloads.
            result = await conn.execute(text("""select
                (select count(*) from public.code_execution_runs where user_id=cast(:user as uuid)
                 and created_at > now() - interval '24 hours') as day_used,
                (select count(*) from public.code_execution_runs where user_id=cast(:user as uuid)
                 and created_at > now() - interval '1 minute') as minute_used,
                (select count(*) from public.code_execution_runs where result is null
                 and created_at > now() - interval '2 minutes') as active"""), dict(user=user))
            counts = result.mappings().one()
            _count_limits(counts["day_used"], counts["minute_used"], counts["active"],
                          self.daily, self.per_minute, self.concurrent)
            run_id = str(uuid.uuid4())
            await conn.execute(text("""insert into public.code_execution_runs
                (id,user_id,scope,idempotency_key,request_hash) values
                (cast(:id as uuid),cast(:user as uuid),:scope,:key,:digest)"""),
                dict(id=run_id, user=user, scope=scope, key=key, digest=digest))
            return run_id, None

    async def finish(self, run_id: str, result: dict):
        async with db.get_engine().begin() as conn:
            await conn.execute(text("""update public.code_execution_runs set
                result=cast(:result as jsonb), finished_at=now() where id=cast(:id as uuid)"""),
                dict(id=run_id, result=json.dumps(result, ensure_ascii=False, allow_nan=False)))

    async def cached(self, user: str, scope: str, digest: str):
        async with db.get_engine().connect() as conn:
            result = await conn.execute(text("""select result from public.code_execution_runs
                where user_id=cast(:user as uuid) and scope=:scope and request_hash=:digest
                and created_at > now() - interval '1 hour' and result is not null
                and result->>'status' <> 'unavailable' order by created_at desc limit 1"""),
                dict(user=user, scope=scope, digest=digest))
            return result.scalar_one_or_none()
