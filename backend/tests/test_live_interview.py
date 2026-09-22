"""A mock interview against the real database, inside one rolled-back transaction (zero residue).

Proves the session SQL: interview_session / session_skill_plan / session_turn upserts with the real enums and
foreign keys, session-scoped metrics and usage rows, profile write-back, and reload after every step.
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text

from app import db
from app.config import get_settings
from app.engine.catalog import load_catalog
from app.engine.providers import LLMRequest, ScriptedProvider
from app.repo import cache
from app.services.interview_service import InterviewConfig, InterviewService
from scripts.seed_db import _seed_in
from tests.livetools import RollbackStore
from tests.test_live_service import SEED_TABLES
from tests.test_practice_hardening import GOOD, SEEDS, WEAK

pytestmark = pytest.mark.skipif(not get_settings().database_url, reason="DATABASE_URL not set")


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


@pytest_asyncio.fixture
async def case(catalog):
    engine = db.get_engine()
    async with engine.connect() as connection:
        outer = await connection.begin()
        await connection.execute(text("select 1"))
        tables = {name: await db.table(name) for name in SEED_TABLES}
        cache.clear()
        await _seed_in(connection, tables, catalog)
        cache.clear()
        user = (await connection.execute(text("select id from public.user_profile limit 1"))).scalar_one()
        try:
            yield {"connection": connection, "catalog": catalog, "user_id": user}
        finally:
            await outer.rollback()
    await db.dispose()


def provider():
    n = {"i": 0}

    def respond(request: LLMRequest):
        if request.role == "evaluator":
            n["i"] += 1
            return WEAK if n["i"] % 3 == 0 else GOOD
        return "## Summary\nlive" if request.role == "report" else "unused"
    return ScriptedProvider(respond)


async def count(connection, sql: str, **params) -> int:
    return (await connection.execute(text(sql), params)).scalar_one()


async def test_a_mock_interview_persists_every_step_in_the_real_schema(case):
    conn, user = case["connection"], case["user_id"]
    svc = InterviewService(RollbackStore(conn), case["catalog"], provider(), InterviewConfig(reviewed_only=False))
    clock = {"now": datetime.now(UTC)}
    svc.clock = lambda: clock["now"]

    started = time.perf_counter()
    view = await svc.start(user, duration_min=20, language="he")
    sid = uuid.UUID(view.id)
    assert await count(conn, "select count(*) from public.interview_session where id = :s", s=sid) == 1
    assert await count(conn, "select count(*) from public.session_skill_plan where session_id = :s", s=sid) == len(view.plan) + \
        await count(conn, "select count(*) from public.session_skill_plan p join public.skill k on k.id = p.skill_id "
                          "where p.session_id = :s and p.assessment_mode = 'observed'", s=sid)
    assert await count(conn, "select count(*) from public.session_turn where session_id = :s", s=sid) == 1

    asked = []
    while view.status == "in_progress" and view.current_turn is not None and len(asked) < 6:
        turn = view.current_turn
        asked.append(turn.question_key)
        if view.can_hint and len(asked) == 1:
            hint, view = await svc.hint(user, sid)
            assert hint is not None
        clock["now"] += timedelta(minutes=3)
        _, view = await svc.answer(user, sid, turn.index, "תשובה מסודרת: הנחות, דרך, תוצאה, בדיקה.", idempotency_key=f"k{turn.index}")
        reloaded = await svc.get(user, sid)                       # every step survives a reload from the database
        assert reloaded.turn_count == view.turn_count and reloaded.status == view.status
    if view.status == "in_progress":
        view = await svc.end(user, sid)
    assert view.status == "completed" and view.results_revealed

    turns = await count(conn, "select count(*) from public.session_turn where session_id = :s and answer_text is not null", s=sid)
    assert turns == len(asked)
    assert await count(conn, "select count(*) from public.evaluation_metrics where session_id = :s", s=sid) == len(asked)
    assert await count(conn, "select count(*) from public.usage_event where session_id = :s", s=sid) == len(asked)  # one evaluator call per turn
    assert await count(conn, "select count(*) from public.user_skill_profile where user_id = :u", u=user) >= 1
    row = (await conn.execute(text("select status, turn_count, hints_used, ended_at, state from public.interview_session where id = :s"),
                              {"s": sid})).one()
    assert row.status == "completed" and row.turn_count == view.turn_count and row.ended_at is not None
    assert row.state["engine"]["turn_index"] == len(asked) and row.hints_used == view.hints_used

    report = await svc.report(user, sid)
    assert report.narrative_md.startswith("## Summary") and report.fit["session_overall"].skills_total >= 1
    answered = [x for x in report.turns if x.status != "skipped"]     # the question left open at "end early" is listed as skipped
    assert len(answered) == len(asked) and all(x.band for x in answered)
    assert time.perf_counter() - started < 240, "an interview of a few turns should not take minutes against the database"
