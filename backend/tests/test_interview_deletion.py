"""Interview deletion hides owned history without erasing learning or accepted work."""
from __future__ import annotations

import asyncio
import copy
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table
from sqlalchemy.dialects.postgresql import JSONB, UUID, dialect

from app.api.errors import ApiError
from app.engine.catalog import load_catalog
from app.engine.providers import ScriptedProvider
from app.repo import sessions
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from tests.test_interview_service import Clock, GOOD, SEEDS, USER, OTHER, interviewer, service


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


async def test_owner_delete_is_idempotent_and_hidden_from_get_report_and_mutations(catalog):
    svc, store = service(catalog, interviewer([GOOD]))
    view = await svc.start(USER, duration_min=20)
    sid = uuid.UUID(view.id)
    with pytest.raises(ApiError) as forbidden:
        await svc.delete(OTHER, sid)
    assert forbidden.value.code == "not_found"
    assert len(await svc.list(USER)) == 1

    await svc.delete(USER, sid)
    deleted_at = store.sessions[sid]["deleted_at"]
    await svc.delete(USER, sid)
    assert store.sessions[sid]["deleted_at"] == deleted_at
    assert await svc.list(USER) == []
    for action in (svc.get(USER, sid), svc.report(USER, sid), svc.hint(USER, sid), svc.end(USER, sid),
                   svc.answer(USER, sid, 0, "answer", idempotency_key="after-delete")):
        with pytest.raises(ApiError) as missing:
            await action
        assert missing.value.code == "not_found"
    assert store.sessions[sid]["turns"][0]["answer_text"] is None


async def test_delete_preserves_scored_turns_skill_progress_usage_and_daily_limit(catalog):
    svc, store = service(catalog, interviewer([GOOD]))
    view = await svc.start(USER, duration_min=20)
    sid = uuid.UUID(view.id)
    svc.clock.advance()
    await svc.answer(USER, sid, 0, "a careful answer", idempotency_key="first")
    await svc.end(USER, sid)
    before = copy.deepcopy({"row": store.sessions[sid]["row"], "turns": store.sessions[sid]["turns"],
                            "profiles": store.profiles, "metrics": store.metrics, "usage": store.usage})
    async with store.transaction() as tx:
        scored_before = await tx.scored_interview_turns(USER)
        starts_before = await tx.sessions_started_today(USER)
    assert scored_before
    await svc.delete(USER, sid)
    assert store.sessions[sid]["row"] == before["row"]
    assert store.sessions[sid]["turns"] == before["turns"]
    assert store.profiles == before["profiles"]
    assert store.metrics == before["metrics"] and store.usage == before["usage"]
    async with store.transaction() as tx:
        assert await tx.scored_interview_turns(USER) == scored_before
        assert await tx.sessions_started_today(USER) == starts_before


async def test_inflight_accepted_evaluation_cannot_restore_deleted_history(catalog):
    entered, release = asyncio.Event(), asyncio.Event()

    async def respond(request):
        if request.role == "evaluator":
            entered.set()
            await release.wait()
            return GOOD
        return "unused"

    store = InMemoryStore(catalog)
    first = InterviewService(store, catalog, ScriptedProvider(respond), InterviewConfig(reviewed_only=False))
    # A second service represents another worker, without sharing the in-process lock.
    second = InterviewService(store, catalog, ScriptedProvider([GOOD]), InterviewConfig(reviewed_only=False))
    first.clock = second.clock = Clock()
    view = await first.start(USER, duration_min=20)
    sid = uuid.UUID(view.id)
    task = asyncio.create_task(first.answer(USER, sid, 0, "saved answer", idempotency_key="accepted"))
    await asyncio.wait_for(entered.wait(), timeout=3)
    try:
        await second.delete(USER, sid)
    finally:
        release.set()
    result, _ = await asyncio.wait_for(task, timeout=3)
    assert result.status == "done"
    assert store.sessions[sid]["deleted_at"] is not None
    assert store.sessions[sid]["turns"][0]["answer_text"] == "saved answer"
    assert store.sessions[sid]["turns"][0]["question_generation_meta"]["status"] == "done"
    assert await second.list(USER) == []
    with pytest.raises(ApiError) as missing:
        await second.get(USER, sid)
    assert missing.value.code == "not_found"


async def test_filtering_precedes_history_limit_and_delete_rolls_back(catalog):
    svc, store = service(catalog, interviewer([GOOD]))
    first = await svc.start(USER, duration_min=20)
    second = await svc.start(USER, duration_min=20)
    sid = uuid.UUID(second.id)
    with pytest.raises(RuntimeError):
        async with store.transaction() as tx:
            assert await tx.delete_session_from_history(sid, user_id=USER)
            raise RuntimeError("rollback")
    assert len(await svc.list(USER)) == 2
    await svc.delete(USER, sid)
    assert [s["id"] for s in await svc.list(USER, limit=1)] == [first.id]


@pytest.mark.parametrize("rowcount,expected", [(0, False), (1, True)])
async def test_database_delete_is_an_owner_scoped_marker_update(monkeypatch, rowcount, expected):
    table = Table("interview_session", MetaData(), Column("id", UUID), Column("user_id", UUID),
                  Column("deleted_at", DateTime(timezone=True)))
    statements = []

    async def get_table(name):
        assert name == "interview_session"
        return table

    async def execute(statement):
        statements.append(statement)
        return SimpleNamespace(rowcount=rowcount)

    monkeypatch.setattr(sessions.db, "table", get_table)
    assert await sessions.delete_from_history(SimpleNamespace(execute=execute), uuid.uuid4(), user_id=USER) is expected
    sql = str(statements[0].compile(dialect=dialect()))
    assert sql.startswith("UPDATE interview_session SET deleted_at=coalesce(")
    assert "interview_session.user_id =" in sql and "interview_session.id =" in sql
    assert "state=" not in sql and "DELETE" not in sql
    assert "deleted_at" not in sessions.SESSION_COLUMNS


async def test_database_history_filters_deleted_rows_before_limit(monkeypatch):
    table = Table("interview_session", MetaData(), Column("id", UUID), Column("user_id", UUID),
                  Column("deleted_at", DateTime(timezone=True)), Column("status", String), Column("config", JSONB),
                  Column("turn_count", Integer), Column("started_at", DateTime), Column("ended_at", DateTime),
                  Column("created_at", DateTime))
    statements = []

    async def get_table(name):
        return table

    async def execute(statement):
        statements.append(statement)
        return SimpleNamespace(all=lambda: [])

    monkeypatch.setattr(sessions.db, "table", get_table)
    assert await sessions.list_sessions(SimpleNamespace(execute=execute), USER, limit=1) == []
    sql = str(statements[0].compile(dialect=dialect()))
    assert "interview_session.deleted_at IS NULL" in sql
    assert sql.index("deleted_at IS NULL") < sql.index("LIMIT")
