"""The production path on the REAL model and the REAL database, with production rules, and zero residue.

Runs inside one database transaction that is rolled back at the end (RollbackStore), so nothing is
written for real; the questions are whatever the database holds right now (status trial or published),
the coach suggests only reviewed/trial questions, the interview asks only those. Costs about $0.40.

    uv run python scripts/e2e_live_trial.py
"""

from __future__ import annotations

import asyncio
import sys
import time
import uuid
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from livetools import RollbackStore  # noqa: E402

from app import db  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.engine.catalog import load_catalog  # noqa: E402
from app.engine.providers import build_provider  # noqa: E402
from app.services.interview_service import InterviewConfig, InterviewService  # noqa: E402
from app.services.practice_service import PracticeService, ServiceConfig  # noqa: E402

WEAK_ANSWER = "alarm = A ^ B ^ C; XOR gives 1 whenever more than one input is 1, so it is the majority."
INTERVIEW_ANSWER = ("I would state the assumptions, derive it step by step from the requirement, write the result and "
                    "check it on the boundary cases. Here: {ref}")


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Windows consoles default to cp1252
    settings = get_settings()
    if not settings.anthropic_api_key or not settings.database_url:
        raise SystemExit("ANTHROPIC_API_KEY and DATABASE_URL are needed")
    provider = build_provider("anthropic", api_key=settings.anthropic_api_key, model=settings.anthropic_model,
                              enable_fallbacks=settings.anthropic_enable_fallbacks, role_models=settings.role_models)
    catalog = load_catalog(settings.seeds_dir)
    started = time.perf_counter()
    async with db.get_engine().connect() as connection:
        outer = await connection.begin()
        await connection.execute(text("select 1"))
        user = (await connection.execute(text("select id from public.user_profile limit 1"))).scalar_one()
        statuses = (await connection.execute(text("select status, count(*) from public.question group by status"))).all()
        print("question statuses in the database:", {s: n for s, n in statuses})
        store = RollbackStore(connection, allow_in_review=False)          # production: no in-review content
        try:
            practice = PracticeService(store, catalog, provider, ServiceConfig(polish_tips=True))   # reviewed-only default
            listed = await practice.list_questions(language="en")
            print(f"servable questions under production rules: {len(listed)} (trial: {sum(q.trial for q in listed)})")

            print("\n=== practice: majority, weak answer, deep mode")
            view = await practice.start(user, question_key="example-sensor-majority", mode="deep", language="en", self_confidence=3)
            aid = uuid.UUID(view.id)
            t = time.perf_counter()
            sub, view = await practice.submit(user, aid, WEAK_ANSWER, idempotency_key="live-main")
            print(f"  main: band={sub.band} in {time.perf_counter() - t:.0f}s, assessed_by={sub.assessed_by}, model={sub.model}")
            print(f"  check: {sub.check.passed if sub.check else None} | follow-up pending: {view.pending_follow_up is not None}")
            if view.pending_follow_up is not None:
                t = time.perf_counter()
                fsub, view = await practice.submit(user, aid, "Majority is at least two of three: AB + BC + AC. XOR is parity.",
                                                   idempotency_key="live-f1", follow_up_turn=view.pending_follow_up.turn)
                print(f"  follow-up: band={fsub.band} in {time.perf_counter() - t:.0f}s")
            print(f"  status={view.status}; next question: "
                  f"{view.next_question.key if view.next_question else None} ({view.next_question.why if view.next_question else '-'})")
            if view.next_question and view.next_question.focus:
                print(f"  focus: {view.next_question.focus}")
            assert view.next_question is not None, "no next question although trial questions exist"

            print("\n=== mock interview: 20 minutes, English, production rules")
            interviews = InterviewService(store, catalog, provider, InterviewConfig(narrative=True))   # reviewed_only default
            iv = await interviews.start(user, duration_min=20, language="en")
            sid = uuid.UUID(iv.id)
            print(f"  plan: {', '.join(p.skill for p in iv.plan)}")
            n = 0
            while iv.status == "in_progress" and iv.current_turn is not None and n < 3:
                turn = iv.current_turn
                n += 1
                ref = catalog.questions[turn.question_key].text("en").reference_solution[:180]
                t = time.perf_counter()
                _, iv = await interviews.answer(user, sid, turn.index, INTERVIEW_ANSWER.format(ref=ref), idempotency_key=f"live-t{turn.index}")
                print(f"  [{turn.index}] {turn.skill_label} ({turn.question_key}, trial={turn.trial}) evaluated in "
                      f"{time.perf_counter() - t:.0f}s → status {iv.status}, remaining {iv.remaining_min} min")
            if iv.status == "in_progress":
                iv = await interviews.end(user, sid)
            t = time.perf_counter()
            report = await interviews.report(user, sid)
            print(f"  report in {time.perf_counter() - t:.0f}s: narrative {report.narrative_source}; "
                  f"fit={ {k: v.fit_score for k, v in report.fit.items()} }; turns={len(report.turns)}")
            rows = (await connection.execute(text("select count(*) from public.session_turn where session_id = :s"), {"s": sid})).scalar_one()
            print(f"  session_turn rows written inside the transaction: {rows}")
        finally:
            await outer.rollback()
            print("\nrolled back: nothing was kept")
    await db.dispose()
    print(f"TOTAL {time.perf_counter() - started:.0f}s wall")


if __name__ == "__main__":
    asyncio.run(main())
