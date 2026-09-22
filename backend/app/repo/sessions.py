"""Mock-interview sessions: `interview_session`, `session_skill_plan`, `session_turn`, plus the
session-scoped metrics and usage rows.

The engine's live state (SessionState) and the service's bookkeeping travel together in
`interview_session.state` as {"engine": ..., "turns": {...}, "metrics": [...], ...}; the plan the
session was built from is frozen in `config["plan"]`. Turns are one row each in `session_turn`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import Integer, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db
from app.repo import cache
from app.repo.events import NOT_COLUMNS, _same_columns

SESSION_COLUMNS = ("seniority", "baseline_difficulty", "difficulty_ceiling", "status", "config", "state", "turn_count",
                   "hints_used", "hints_requested_by_user", "started_at", "ended_at")
TURN_COLUMNS = ("question_archetype", "difficulty", "question_text", "expected_answer_outline", "question_generation_meta",
                "answer_text", "answer_code", "answer_language", "check_result", "answer_started_at", "answer_submitted_at")


class StaleSession(Exception):
    """The session row changed under us (another server or tab wrote first); reload and redo."""


@dataclass
class StoredSession:
    id: uuid.UUID
    user_id: uuid.UUID
    row: dict                                   # SESSION_COLUMNS + id
    turns: list[dict] = field(default_factory=list)   # ordered by turn_index; keys: turn_index, skill_key, question_key, TURN_COLUMNS


def _iso(value):
    return value.isoformat() if isinstance(value, datetime) else value


def _dt(value):
    return datetime.fromisoformat(value) if isinstance(value, str) else value


async def _ids(connection: AsyncConnection, table_name: str, key_column: str = "key") -> dict[str, uuid.UUID]:
    async def load():
        table = await db.table(table_name)
        return {getattr(row, key_column): row.id
                for row in await connection.execute(select(table.c.id, getattr(table.c, key_column)))}
    return await cache.ID_MAPS.get(f"{table_name}_ids_{key_column}", load)


async def _versioned_id(connection: AsyncConnection, table_name: str, slug: str) -> tuple[uuid.UUID, int]:
    table = await db.table(table_name)
    row = (await connection.execute(select(table.c.id, table.c.version).where(table.c.slug == slug))).first()
    if row is None:
        raise LookupError(f"{table_name} {slug!r} is not in the database")
    return row.id, row.version


async def load(connection: AsyncConnection, session_id: uuid.UUID, *, user_id: uuid.UUID) -> StoredSession | None:
    session, turn = await db.table("interview_session"), await db.table("session_turn")
    skill, question = await db.table("skill"), await db.table("question")
    row = (await connection.execute(select(session).where(session.c.id == session_id, session.c.user_id == user_id))).first()
    if row is None:
        return None
    turns = (await connection.execute(
        select(turn, skill.c.key.label("skill_key"), question.c.key.label("question_key"))
        .join(skill, skill.c.id == turn.c.skill_id).outerjoin(question, question.c.id == turn.c.question_id)
        .where(turn.c.session_id == session_id).order_by(turn.c.turn_index))).all()
    return StoredSession(
        id=row.id, user_id=row.user_id,
        row={"id": str(row.id), **{c: _iso(getattr(row, c)) for c in SESSION_COLUMNS}},
        turns=[{"turn_index": t.turn_index, "skill_key": t.skill_key,
                # the bank key travels in the meta as well, so a turn survives a question row being re-keyed
                "question_key": t.question_key or (t.question_generation_meta or {}).get("question_key"),
                "question_id": str(t.question_id) if t.question_id else None, "created_at": _iso(t.created_at),
                **{c: _iso(getattr(t, c)) for c in TURN_COLUMNS}} for t in turns])


async def save(connection: AsyncConnection, *, user_id: uuid.UUID, row: dict, turns: list[dict], plan: list[dict] | None,
               role_slug: str, company_slug: str, expected_revision: int | None = None) -> None:
    """Write the session row and the given turns; the skill plan rows once (when `plan` is given).

    With `expected_revision` the session row is UPDATED only if its stored `state.revision` still equals it
    (raises StaleSession otherwise); without it the row is inserted (or replaced) unconditionally."""
    session, turn, plan_table = await db.table("interview_session"), await db.table("session_turn"), await db.table("session_skill_plan")
    skill_ids = await _ids(connection, "skill")
    role_id, role_version = await _versioned_id(connection, "role_template", role_slug)
    company_id, company_version = await _versioned_id(connection, "company_profile", company_slug)
    values = {"id": row["id"], "user_id": user_id, "role_template_id": role_id, "role_template_version": role_version,
              "company_profile_id": company_id, "company_profile_version": company_version,
              **{c: row.get(c) for c in SESSION_COLUMNS}}
    for c in ("started_at", "ended_at"):
        values[c] = _dt(values.get(c))
    if expected_revision is None:
        statement = insert(session).values(**db.sql_values(values))
        updates = {c: statement.excluded[c] for c in SESSION_COLUMNS}
        await connection.execute(statement.on_conflict_do_update(index_elements=["id"], set_=updates))
    else:
        columns = db.sql_values({c: values[c] for c in SESSION_COLUMNS})
        result = await connection.execute(
            update(session).where(session.c.id == row["id"], session.c.user_id == user_id,
                                  func.coalesce(session.c.state["revision"].astext.cast(Integer), 0) == expected_revision)
            .values(**columns))
        if result.rowcount != 1:
            raise StaleSession(f"interview {row['id']} moved past revision {expected_revision}")

    if plan:
        rows = [{"session_id": row["id"], "skill_id": skill_ids[p["key"]], "source": p["source"],
                 "role_weight": p.get("role_weight", 0.0), "company_weight": p.get("company_weight", 0.0),
                 "combined_weight": p["combined_weight"], "importance": p["importance"], "required_level": p["required_level"],
                 "assessment_mode": p["assessment_mode"], "planned_turns": p.get("planned_turns", 0),
                 "priority_rank": p.get("priority_rank"), "examination_notes": p.get("examination_notes")} for p in plan]
        if rows:
            await connection.execute(insert(plan_table).on_conflict_do_nothing(index_elements=["session_id", "skill_id"]), rows)

    for t in turns:
        values = {"session_id": row["id"], "turn_index": t["turn_index"], "skill_id": skill_ids[t["skill_key"]],
                  "question_id": t.get("question_id"), **{c: t.get(c) for c in TURN_COLUMNS}}
        for c in ("answer_started_at", "answer_submitted_at"):
            values[c] = _dt(values.get(c))
        statement = insert(turn).values(**db.sql_values(values))
        updates = {c: statement.excluded[c] for c in TURN_COLUMNS}
        await connection.execute(statement.on_conflict_do_update(index_elements=["session_id", "turn_index"], set_=updates))


async def list_sessions(connection: AsyncConnection, user_id: uuid.UUID, *, limit: int = 20) -> list[dict]:
    session = await db.table("interview_session")
    rows = (await connection.execute(
        select(session.c.id, session.c.status, session.c.config, session.c.turn_count, session.c.started_at, session.c.ended_at)
        .where(session.c.user_id == user_id).order_by(session.c.created_at.desc()).limit(limit))).all()
    return [{"id": str(r.id), "status": r.status, "duration_min": (r.config or {}).get("duration_min"),
             "language": (r.config or {}).get("language"), "turn_count": r.turn_count,
             "started_at": _iso(r.started_at), "ended_at": _iso(r.ended_at)} for r in rows]


async def started_today(connection: AsyncConnection, user_id: uuid.UUID, *, now: datetime | None = None) -> int:
    session = await db.table("interview_session")
    now = now or datetime.now(UTC)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return (await connection.execute(
        select(func.count()).select_from(session)
        .where(session.c.user_id == user_id, session.c.created_at >= day_start))).scalar_one()


async def record_metrics(connection: AsyncConnection, *, user_id: uuid.UUID, session_id: uuid.UUID, metrics: list[dict],
                         seniority: str | None, role_slug: str, company_slug: str) -> int:
    """evaluation_metrics rows for interview turns: session-scoped, no attempt. Simulation rows must carry the
    role, company, family and seniority context (evaluation_metrics_session_context_chk)."""
    table = await db.table("evaluation_metrics")
    skill_ids = await _ids(connection, "skill")
    role = await db.table("role_template")
    role_row = (await connection.execute(
        select(role.c.id, role.c.version, role.c.family, role.c.sub_family).where(role.c.slug == role_slug))).first()
    if role_row is None:
        raise LookupError(f"role_template {role_slug!r} is not in the database")
    company_id, _ = await _versioned_id(connection, "company_profile", company_slug)
    columns = set(table.c.keys())
    rows = []
    for metric in metrics:
        row = {k: v for k, v in metric.items() if k in columns and k not in NOT_COLUMNS}
        row.update({
            "user_id": user_id, "session_id": session_id, "attempt_id": None, "turn_index": metric.get("turn_index"),
            "role_template_id": role_row.id, "role_template_version": role_row.version, "company_profile_id": company_id,
            "family": role_row.family, "sub_family": role_row.sub_family,
            "subject_id": skill_ids[metric["subject_key"]], "skill_id": skill_ids[metric["skill_key"]],
            "seniority": seniority, "subject_switch": bool(metric.get("subject_switch", False)),
            "hint_requested_by_user": bool(metric.get("hint_requested_by_user", False)),
            "eval_flags": list(metric.get("eval_flags") or []),
        })
        if metric.get("skill_next_key"):
            row["skill_next_id"] = skill_ids.get(metric["skill_next_key"])
        if metric.get("subject_next_key"):
            row["subject_next_id"] = skill_ids.get(metric["subject_next_key"])
        rows.append(row)
    if rows:
        await connection.execute(insert(table), _same_columns(rows))
    return len(rows)


async def record_usage(connection: AsyncConnection, *, user_id: uuid.UUID, session_id: uuid.UUID, usage_rows: list[dict]) -> int:
    table = await db.table("usage_event")
    if usage_rows:
        await connection.execute(insert(table), _same_columns([{"user_id": user_id, "session_id": session_id, **row}
                                                               for row in usage_rows]))
    return len(usage_rows)
