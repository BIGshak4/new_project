"""The real database under many users at once. Nothing is written for real: every unit of work is rolled back.

    1. connections  N connections opened at the same moment through the Session pooler, each runs `select 1` and
                    holds its connection for a second: where does the pooler start refusing or queueing clients?
    2. flows        N users at once, each on its own connection inside one rolled-back transaction, walking the
                    service: start an attempt, read it, submit (scripted model: no model time, no cost), progress,
                    program. Virtual users are spread over the real accounts (only a few exist), so users that share
                    an account also share its skill-profile rows; a write to one waits for the other to roll back.
    3. pool         the API's own pool (app/db.py: pool_size 5, max_overflow 5) shared by N users who each read the
                    progress page's data (the heaviest read set, read-only) five times: how long does a request
                    wait for a connection, and how long does it hold one?

Every statement is a round trip. From Shaked's machine one round trip is ~70 ms; from Render (same Frankfurt region
as the database) it is a few ms, so hold times here are that ratio larger than in production. The report says both.

    uv run python scripts/db_concurrency.py --phase connections --users 5 10 15 20 30
    uv run python scripts/db_concurrency.py --phase flows --users 1 5 10 20
    uv run python scripts/db_concurrency.py --phase pool --users 5 10 20 40
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from livetools import RollbackStore  # noqa: E402

from app import db  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.engine.catalog import load_catalog  # noqa: E402
from app.engine.providers import LLMRequest, ScriptedProvider  # noqa: E402
from app.repo import cache  # noqa: E402
from app.services.practice_service import PracticeService, ServiceConfig  # noqa: E402
from app.services.store import DbTx  # noqa: E402

GOOD = {"correctness": 0.9, "depth": 0.8, "clarity": 0.7, "structure": 0.6, "tradeoff_reasoning": 0.5,
        "risk_awareness": 0.5, "hedging_ratio": 0.2, "rubric_level_estimate": 4, "key_points_hit": ["x"],
        "key_points_missed": [], "misconceptions": [], "behavior_signals": [], "one_line_summary": "ok"}
KEYS = ["example-sensor-majority", "example-nand-only-enable", "example-masked-equality", "example-enabled-decoder"]


def scripted() -> ScriptedProvider:
    def respond(request: LLMRequest):
        return {"evaluator": GOOD, "feedback": {"what_happened": "w", "why_it_matters": "y", "next_step": "n",
                                                "your_reasoning_vs_reference": "c"},
                "generator": {"question_text": "Why?", "question_archetype": "design", "expected_answer_outline": "x",
                              "rubric_focus": []}}.get(request.role, "tip")
    return ScriptedProvider(respond)


PORT: int | None = None                                        # --port 6543: the transaction pooler instead of session


def database_url() -> str:
    url = db.normalize_url(get_settings().database_url)
    if PORT is not None:
        url = re.sub(r"(@[^:/]+):[0-9]+", lambda m: f"{m.group(1)}:{PORT}", url)
    return url


def fresh_engine(pool_size: int, max_overflow: int, pool_timeout: float = 30):
    return create_async_engine(database_url(), pool_pre_ping=True, pool_size=pool_size,
                               max_overflow=max_overflow, pool_timeout=pool_timeout,
                               connect_args={"statement_cache_size": 0})


def pct(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(p * (len(ordered) - 1))))] if ordered else 0.0


async def real_users() -> list[uuid.UUID]:
    async with db.get_engine().connect() as connection:
        rows = (await connection.execute(text("select id from public.user_profile order by created_at"))).all()
        await connection.rollback()
    return [r.id for r in rows]


# ---------------------------------------------------------------------------------------------- 1. connections


async def phase_connections(n: int) -> str:
    engine = fresh_engine(pool_size=n, max_overflow=0)
    connect_ms, errors = [], defaultdict(int)
    barrier = asyncio.Event()

    async def one():
        await barrier.wait()
        started = time.perf_counter()
        try:
            async with engine.connect() as connection:
                await connection.execute(text("select 1"))
                connect_ms.append((time.perf_counter() - started) * 1000)
                await asyncio.sleep(1.0)                       # hold it, as a busy API would
                await connection.rollback()
        except Exception as exc:                               # noqa: BLE001 - the finding
            errors[f"{type(exc).__name__}: {str(exc).splitlines()[0][:90]}"] += 1
    tasks = [asyncio.create_task(one()) for _ in range(n)]
    await asyncio.sleep(0.05)
    started = time.perf_counter()
    barrier.set()
    await asyncio.gather(*tasks)
    wall = time.perf_counter() - started
    await engine.dispose()
    line = (f"| {n} | {len(connect_ms)} | {pct(connect_ms, .5):.0f} ms | {pct(connect_ms, .95):.0f} ms | "
            f"{max(connect_ms, default=0):.0f} ms | {wall:.1f} s | {'; '.join(f'{k} ×{v}' for k, v in errors.items())} |")
    return line


# ---------------------------------------------------------------------------------------------- 2. flows


async def phase_flows(n: int, users: list[uuid.UUID], catalog) -> tuple[str, dict]:
    engine = fresh_engine(pool_size=n, max_overflow=0)
    times: dict[str, list[float]] = defaultdict(list)
    errors: dict[str, int] = defaultdict(int)

    async def one(index: int):
        user = users[index % len(users)]
        async with engine.connect() as connection:
            outer = await connection.begin()
            try:
                svc = PracticeService(RollbackStore(connection, allow_in_review=False), catalog, scripted(),
                                      ServiceConfig(daily_attempt_limit=100_000, feedback_in_background=True))
                steps = [("start", lambda: svc.start(user, question_key=KEYS[index % len(KEYS)], mode="deep"))]
                started = time.perf_counter()
                view = await steps[0][1]()
                times["start"].append((time.perf_counter() - started) * 1000)
                aid = uuid.UUID(view.id)
                for name, action in (("get", lambda: svc.get(user, aid)),
                                     ("submit (scripted model)", lambda: svc.submit(user, aid, "an answer",
                                                                                    idempotency_key=f"{aid}")),
                                     ("words saved", lambda: svc.drain()),
                                     ("progress", lambda: svc.progress(user)),
                                     ("program", lambda: svc.program(user))):
                    started = time.perf_counter()
                    await action()
                    times[name].append((time.perf_counter() - started) * 1000)
            except Exception as exc:                           # noqa: BLE001 - the finding
                errors[f"{type(exc).__name__}: {str(exc).splitlines()[0][:90]}"] += 1
            finally:
                await outer.rollback()

    started = time.perf_counter()
    await asyncio.gather(*[one(i) for i in range(n)])
    wall = time.perf_counter() - started
    await engine.dispose()
    cells = " | ".join(f"{pct(times[k], .5):.0f} / {pct(times[k], .95):.0f}" for k in
                       ("start", "get", "submit (scripted model)", "words saved", "progress", "program"))
    return (f"| {n} | {cells} | {wall:.1f} s | {'; '.join(f'{k} ×{v}' for k, v in errors.items())} |",
            {k: v for k, v in times.items()})


# ---------------------------------------------------------------------------------------------- 3. the API's pool


async def progress_reads(tx: DbTx, user: uuid.UUID) -> None:
    """What progress() reads, read-only (its plan rebuild is a write and is left out)."""
    await tx.load_profile(user)
    await tx.recent_attempts(user, limit=60)
    await tx.started_today(user)
    await tx.load_goal(user)
    await tx.band_counts(user)
    await tx.daily_bands(user)
    await tx.list_questions(language="en")
    await tx.scored_submissions(user)
    await tx.scored_interview_turns(user)
    await tx.load_active_plan(user)


async def phase_pool(n: int, users: list[uuid.UUID], rounds: int = 5) -> str:
    engine = fresh_engine(pool_size=5, max_overflow=5)          # app/db.py
    waits, holds, errors = [], [], defaultdict(int)

    @asynccontextmanager
    async def unit():
        asked = time.perf_counter()
        async with engine.connect() as connection:
            got = time.perf_counter()
            waits.append((got - asked) * 1000)
            outer = await connection.begin()
            try:
                yield DbTx(connection, allow_in_review=False)
            finally:
                await outer.rollback()
                holds.append((time.perf_counter() - got) * 1000)

    async def one(index: int):
        user = users[index % len(users)]
        for _ in range(rounds):
            try:
                async with unit() as tx:
                    await progress_reads(tx, user)
            except Exception as exc:                           # noqa: BLE001 - the finding
                errors[f"{type(exc).__name__}: {str(exc).splitlines()[0][:90]}"] += 1
            await asyncio.sleep(0.2)                           # a user reads the page before the next click

    started = time.perf_counter()
    await asyncio.gather(*[one(i) for i in range(n)])
    wall = time.perf_counter() - started
    await engine.dispose()
    done = len(holds)
    return (f"| {n} | {done} | {pct(waits, .5):.0f} ms | {pct(waits, .95):.0f} ms | {max(waits, default=0):.0f} ms | "
            f"{pct(holds, .5):.0f} ms | {done / wall:.1f}/s | {'; '.join(f'{k} ×{v}' for k, v in errors.items())} |")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--phase", choices=["connections", "flows", "pool"], required=True)
    parser.add_argument("--users", type=int, nargs="+", required=True)
    parser.add_argument("--port", type=int, help="5432 = Session pooler (today), 6543 = Transaction pooler")
    args = parser.parse_args()
    global PORT
    PORT = args.port
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    catalog = load_catalog(get_settings().seeds_dir)
    users = await real_users()
    await db.get_metadata()
    print(f"real accounts: {len(users)}; pooler port {PORT or 'as configured'}", flush=True)
    if args.phase == "connections":
        print("| connections at once | opened | connect p50 | p95 | max | wall | errors |\n|---:|---:|---:|---:|---:|---:|---|",
              flush=True)
        for n in args.users:
            print(await phase_connections(n), flush=True)
            await asyncio.sleep(2)
    elif args.phase == "flows":
        print("| users | start | get | submit | words saved | progress | program | wall | errors |\n"
              "|---:|---:|---:|---:|---:|---:|---:|---:|---|  (p50 / p95 ms)", flush=True)
        for n in args.users:
            cache.clear()
            line, _ = await phase_flows(n, users, catalog)
            print(line, flush=True)
    else:
        print("| users | reads done | wait p50 | wait p95 | wait max | hold p50 | throughput | errors |\n"
              "|---:|---:|---:|---:|---:|---:|---:|---|", flush=True)
        for n in args.users:
            print(await phase_pool(n, users), flush=True)
    await db.dispose()


if __name__ == "__main__":
    asyncio.run(main())
