"""Where the time goes.

    uv run python scripts/profile_service.py --cpu      # engine + service CPU hotspots, in memory, cProfile
    uv run python scripts/profile_service.py --db       # SQL statements and wall time per user action, live
                                                        # Supabase, inside one rolled-back transaction

The --db numbers are what a user feels: each statement is a round trip to a remote database.
"""

from __future__ import annotations

import argparse
import asyncio
import cProfile
import pstats
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.engine.catalog import load_catalog  # noqa: E402
from app.engine.providers import LLMRequest, ScriptedProvider  # noqa: E402
from app.services.memory_store import InMemoryStore  # noqa: E402
from app.services.practice_service import PracticeService, ServiceConfig  # noqa: E402

SEEDS = Path(__file__).resolve().parent.parent / "seeds"
GOOD = {"correctness": 0.9, "depth": 0.8, "clarity": 0.7, "structure": 0.6, "tradeoff_reasoning": 0.5,
        "risk_awareness": 0.5, "hedging_ratio": 0.2, "rubric_level_estimate": 4, "key_points_hit": ["x"],
        "key_points_missed": [], "misconceptions": [], "behavior_signals": [], "one_line_summary": "ok"}
WEAK = {**GOOD, "correctness": 0.2, "depth": 0.2, "rubric_level_estimate": 2, "misconceptions": ["xor_confused_with_majority"]}
CARD = {"what_happened": "w", "why_it_matters": "y", "next_step": "n", "your_reasoning_vs_reference": "c"}
FOLLOW_UP = {"question_text": "And from S3 on input 0?", "question_archetype": "design",
             "expected_answer_outline": "S2", "rubric_focus": []}


def provider(evaluation=WEAK) -> ScriptedProvider:
    def respond(request: LLMRequest):
        return {"evaluator": evaluation, "generator": FOLLOW_UP, "feedback": CARD}.get(request.role, "tip text")
    return ScriptedProvider(respond)


async def one_loop(svc: PracticeService, user: uuid.UUID, key: str) -> None:
    view = await svc.start(user, question_key=key)
    aid = uuid.UUID(view.id)
    await svc.next_hint(user, aid)
    _, view = await svc.submit(user, aid, "alarm = A ^ B ^ C", idempotency_key=f"{aid}-m")
    turns = 0
    while view.pending_follow_up is not None and turns < 2:
        _, view = await svc.submit(user, aid, "follow-up", idempotency_key=f"{aid}-f{turns}",
                                   follow_up_turn=view.pending_follow_up.turn)
        turns += 1
    await svc.get(user, aid)
    await svc.progress(user)


async def cpu_profile(loops: int) -> None:
    catalog = load_catalog(SEEDS)
    store = InMemoryStore(catalog)
    svc = PracticeService(store, catalog, provider(), ServiceConfig(daily_attempt_limit=10_000))
    keys = list(catalog.questions)
    user = uuid.uuid4()
    started = time.perf_counter()
    profiler = cProfile.Profile()
    profiler.enable()
    for i in range(loops):
        await one_loop(svc, user, keys[i % len(keys)])
    profiler.disable()
    elapsed = time.perf_counter() - started
    print(f"{loops} full loops in {elapsed:.2f}s = {elapsed / loops * 1000:.0f} ms per loop (in memory, no model latency)\n")
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumulative")
    print("--- top by cumulative time (app code only)")
    stats.print_stats(r"\\app\\|/app/", 25)
    stats.sort_stats("tottime")
    print("--- top by own time (everything)")
    stats.print_stats(15)


async def db_profile() -> None:
    from sqlalchemy import event, text

    from app import db
    from app.repo import cache
    from tests.livetools import RollbackStore

    catalog = load_catalog(SEEDS)
    engine = db.get_engine()
    statements: list[str] = []

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def _count(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.split("\n")[0][:60])

    async with engine.connect() as connection:
        outer = await connection.begin()
        await connection.execute(text("select 1"))
        user = (await connection.execute(text("select id from public.user_profile limit 1"))).scalar_one()
        svc = PracticeService(RollbackStore(connection), catalog, provider(), ServiceConfig(daily_attempt_limit=10_000))
        cache.clear()

        async def measure(name, coroutine):
            statements.clear()
            started = time.perf_counter()
            result = await coroutine
            ms = (time.perf_counter() - started) * 1000
            print(f"  {name:<28} {len(statements):>3} statements  {ms:>6.0f} ms")
            return result

        print("cold (caches empty):")
        view = await measure("start", svc.start(user, question_key="example-sensor-majority"))
        aid = uuid.UUID(view.id)
        await measure("next_hint", svc.next_hint(user, aid))
        _, view = await measure("submit (main)", svc.submit(user, aid, "alarm = A ^ B ^ C", idempotency_key="m"))
        if view.pending_follow_up:
            await measure("submit (follow-up)", svc.submit(user, aid, "fu", idempotency_key="f1",
                                                          follow_up_turn=view.pending_follow_up.turn))
        await measure("get (refresh)", svc.get(user, aid))
        await measure("submit (replay)", svc.submit(user, aid, "alarm = A ^ B ^ C", idempotency_key="m"))
        await measure("progress", svc.progress(user))
        await measure("list_questions", svc.list_questions(language="en"))
        print("warm (second question, caches filled):")
        view = await measure("start", svc.start(user, question_key="example-nand-only-enable"))
        aid = uuid.UUID(view.id)
        await measure("next_hint", svc.next_hint(user, aid))
        await measure("submit (main)", svc.submit(user, aid, "a NAND-only answer", idempotency_key="m2"))
        await measure("get (refresh)", svc.get(user, aid))
        await measure("list_questions", svc.list_questions(language="he"))
        await outer.rollback()
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--db", action="store_true")
    parser.add_argument("--loops", type=int, default=200)
    args = parser.parse_args()
    if args.cpu:
        asyncio.run(cpu_profile(args.loops))
    if args.db:
        asyncio.run(db_profile())
    if not (args.cpu or args.db):
        parser.print_help()


if __name__ == "__main__":
    main()
