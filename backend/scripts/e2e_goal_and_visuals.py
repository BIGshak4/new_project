"""The 2026-09-23 features on the REAL model and the REAL database, production rules, zero residue.

Inside one transaction that is rolled back (RollbackStore): the goal is saved on the real profile row, the
library is listed by job type (relevance order), company sightings degrade cleanly while their table is not
applied (readers empty, writer 503) or work once it is, the progress view has its three parts, and a mock
interview turn is answered with a DRAWN circuit and scored by the real evaluator. Costs about $0.15.

    uv run python scripts/e2e_goal_and_visuals.py
"""

from __future__ import annotations

import asyncio
import sys
import time
import uuid
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from livetools import RollbackStore  # noqa: E402
from test_visual_assessment import majority_circuit  # noqa: E402

from app import db  # noqa: E402
from app.api.errors import ApiError  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.engine.catalog import load_catalog  # noqa: E402
from app.engine.providers import build_provider  # noqa: E402
from app.repo import sightings  # noqa: E402
from app.services.interview_service import InterviewConfig, InterviewService  # noqa: E402
from app.services.practice_service import PracticeService, ServiceConfig  # noqa: E402

ANSWER = "I would build it from the requirement and check the boundary cases; the drawing shows my circuit."


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
        user = (await connection.execute(text("select id from public.user_profile limit 1"))).scalar_one()
        store = RollbackStore(connection, allow_in_review=False)
        try:
            practice = PracticeService(store, catalog, provider, ServiceConfig(polish_tips=True))
            table_present = await sightings.available()
            print(f"question_sighting table applied: {table_present}")

            print("\n=== the goal, on the real profile row (rolled back)")
            goal = await practice.save_goal(user, job_type="verification", interview_date=date.today() + timedelta(days=12),
                                            minutes_per_day=20, seniority="junior", language="en")
            print(f"  saved: {goal.job_type_label}, {goal.days_to_interview} days, {goal.minutes_per_day} min/day, complete={goal.complete}")
            again = await practice.get_goal(user, language="he")
            assert again.job_type == "verification" and again.job_type_label == "וריפיקציה", again

            print("\n=== the library by job type")
            everything = await practice.list_questions(language="en")
            by_job = await practice.list_questions(language="en", job="verification")
            print(f"  all: {len(everything)} · verification: {len(by_job)} · first: {by_job[0].key} (relevance {by_job[0].relevance})")
            assert all("verification" in q.job_types for q in by_job)
            assert [q.relevance for q in by_job] == sorted((q.relevance for q in by_job), reverse=True)
            assert all(q.companies == [] for q in everything) or table_present

            print("\n=== company sightings")
            try:
                tags = await practice.add_sighting(user, company="Intel", key=everything[0].key)
                print(f"  added (table applied): {[t.model_dump() for t in tags]}")
                assert table_present
            except ApiError as exc:
                print(f"  writer refused as designed: {exc.code} {exc.status} ({exc.message})")
                assert exc.code == "temporarily_unavailable" and not table_present
            print(f"  companies(): {await practice.companies()}")

            print("\n=== progress: overview / timeline / plan / goal")
            progress = await practice.progress(user, language="en")
            o = progress.overview
            print(f"  overview: {o.level} (rank {o.level_rank}) · answered {o.answered} · strong {o.strong} · skills {o.skills_assessed}/{o.skills_total}")
            print(f"  message: {o.message}")
            print(f"  timeline points: {len(progress.timeline)}; last: {progress.timeline[-1].model_dump() if progress.timeline else None}")
            print(f"  plan: {len(progress.plan.items)} items over days {sorted({i.day_index for i in progress.plan.items})}, "
                  f"{progress.plan.minutes_per_day} min/day, {progress.plan.days_to_interview} days to interview")
            for item in progress.plan.items[:4]:
                print(f"    day {item.day_index} · {item.mode} · {', '.join(s.label for s in item.skills)} · {item.minutes} min · {item.reason}")
            assert progress.goal.complete and progress.plan.minutes_per_day == 20
            assert progress.plan.items, "30 trial questions exist: the plan must not be empty"

            print("\n=== mock interview: a turn answered with a drawn circuit, real evaluator")
            interviews = InterviewService(store, catalog, provider, InterviewConfig(narrative=False))
            iv = await interviews.start(user, duration_min=20, language="en")
            sid = uuid.UUID(iv.id)
            turn = iv.current_turn
            print(f"  plan follows the goal: job_type recorded = "
                  f"{(await connection.execute(text("select config->>'job_type' from public.interview_session where id = :s"), {'s': sid})).scalar_one()}")
            t = time.perf_counter()
            answer = {"text": ANSWER, "visual": {"circuit": majority_circuit(), "images": []}}
            result, iv = await interviews.answer(user, sid, turn.index, answer, idempotency_key="draw-1")
            print(f"  [{turn.index}] {turn.skill_label} ({turn.question_key}) → {result.status} in {time.perf_counter() - t:.0f}s; "
                  f"flags={result.flags}; visual kept={result.visual is not None}")
            assert result.status == "done" and "circuit_assessed" in result.flags and result.visual is not None
            meta = (await connection.execute(text(
                "select question_generation_meta->'answer_visual' from public.session_turn where session_id = :s and turn_index = :i"),
                {"s": sid, "i": turn.index})).scalar_one()
            assert meta and meta.get("circuit"), "the drawing was not stored on the turn"
            print(f"  stored answer_visual parts: {len(meta['circuit']['parts'])}")
            iv = await interviews.end(user, sid)
            report = await interviews.report(user, sid, narrative=False)
            shown = next(x for x in report.turns if x.index == turn.index)
            print(f"  report reveals band={shown.band}, visual in report={shown.visual is not None}, check={shown.check.passed if shown.check else None}")
        finally:
            await outer.rollback()
            print("\nrolled back: nothing was kept")
    await db.dispose()
    print(f"TOTAL {time.perf_counter() - started:.0f}s wall")


if __name__ == "__main__":
    asyncio.run(main())
