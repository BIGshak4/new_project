"""Attempts and their answer revisions.

`PracticeAttempt.attempt_row()` is the unit of persistence; this module splits it over
`attempt` (one row) and `attempt_submission` (one row per revision) and joins it back.
The database's unique (attempt_id, idempotency_key) is the cross-process half of
"scored exactly once": a second server accepting the same key fails the insert
instead of creating a second revision.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db

SUBMISSION_COLUMNS = ("revision", "key", "turn", "answer", "hints_seen", "reference_seen", "exposure_sequence", "status",
                      "attempts", "accepted_at", "evaluated_at", "band", "evaluation", "flags", "check", "evidence_weight",
                      "card", "tip_key", "tip_text", "follow_up")


class DuplicateSubmissionKey(Exception):
    """Another process already accepted a revision with this idempotency key, or took this revision number."""


class AlreadyEvaluated(Exception):
    """Another process finished evaluating this revision first; the caller must reload and replay it."""


@dataclass
class StoredAttempt:
    id: uuid.UUID
    user_id: uuid.UUID
    question_id: uuid.UUID
    question_key: str
    started_at: datetime
    row: dict                                  # exactly what PracticeAttempt.restore() takes


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _submission_row(attempt_id: uuid.UUID, s: dict) -> dict:
    return {
        "attempt_id": attempt_id, "revision": s["revision"], "idempotency_key": s["key"], "turn": s["turn"],
        "answer": s["answer"], "visual_answer": s.get("visual"), "hints_seen": s["hints_seen"], "reference_seen": s["reference_seen"],
        "exposure_sequence": s["exposure_sequence"], "status": s["status"], "attempts": s["attempts"],
        "accepted_at": _dt(s["accepted_at"]), "evaluated_at": _dt(s.get("evaluated_at")), "band": s.get("band"),
        "evaluation": s.get("evaluation"), "check_result": s.get("check"), "evidence_weight": s.get("evidence_weight", 0.0),
        "card": s.get("card"), "tip_key": s.get("tip_key"), "tip_text": s.get("tip_text"), "follow_up": s.get("follow_up"),
        "flags": list(s.get("flags") or []), "evaluator_model": s.get("evaluator_model"),
    }


def _submission_dict(row) -> dict:
    return {
        "revision": row.revision, "key": row.idempotency_key, "turn": row.turn, "answer": row.answer, "visual": row.visual_answer,
        "hints_seen": row.hints_seen, "reference_seen": row.reference_seen, "exposure_sequence": row.exposure_sequence,
        "status": row.status, "attempts": row.attempts, "accepted_at": _iso(row.accepted_at),
        "evaluated_at": _iso(row.evaluated_at), "band": row.band, "evaluation": row.evaluation,
        "flags": list(row.flags or []), "check": row.check_result, "evidence_weight": float(row.evidence_weight or 0),
        "card": row.card, "tip_key": row.tip_key, "tip_text": row.tip_text, "follow_up": row.follow_up,
        "evaluator_model": row.evaluator_model,
    }


async def save(connection: AsyncConnection, *, user_id: uuid.UUID, question_id: uuid.UUID, row: dict,
               revisions: set[int] | None = None, known_revisions: int = 0) -> None:
    """Upsert the attempt and its revisions.

    `revisions` limits which revisions are written (None = all); `known_revisions` is how many were
    already in the database when the attempt was loaded, so only genuinely new rows need the
    savepoint that turns a refused idempotency key into DuplicateSubmissionKey.
    """
    attempt, submission = await db.table("attempt"), await db.table("attempt_submission")
    main = next((s for s in reversed(row["submissions"]) if s["turn"] == 0), None)
    values = {
        "id": uuid.UUID(str(row["id"])), "user_id": user_id, "question_id": question_id,
        "question_version": row["question_version"], "mode": row["mode"], "practice_language": row["practice_language"],
        "self_confidence_before": row.get("self_confidence_before"), "answer": row.get("answer"),
        "check_result": row.get("check_result"), "evaluation": row.get("evaluation"), "band": row.get("band"),
        "hints_used": row["hints_used"], "reference_revealed": row["reference_revealed"],
        "revealed_before_submit": row["revealed_before_submit"], "follow_up_turns": row["follow_up_turns"],
        "misconceptions_hit": list(row.get("misconceptions_hit") or []), "familiarity": row["familiarity"],
        "duration_ms": row.get("duration_ms"), "submitted_at": _dt(main["accepted_at"]) if main else None,
        "exposures": row.get("exposures") or [],
        "engine_state": {"evidence_mode": row.get("evidence_mode"), "tip_turns": row.get("tip_turns") or {},
                         "next_question": row.get("next_question"),
                         # attempt_submission has no column for this; it lives here, keyed by revision
                         "evaluating_since": {str(s["revision"]): s["evaluating_since"] for s in row["submissions"]
                                              if s.get("evaluating_since")}},
    }
    statement = insert(attempt).values(**db.sql_values(values))
    updates = {c: statement.excluded[c] for c in values if c not in ("id", "user_id", "question_id", "started_at")}
    await connection.execute(statement.on_conflict_do_update(index_elements=["id"], set_=updates))

    for s in row["submissions"]:
        if revisions is not None and s["revision"] not in revisions:
            continue
        sub = _submission_row(values["id"], s)
        if s["revision"] > known_revisions:
            # a NEW revision: a plain insert. If another process took this revision number or this key
            # first, DO NOTHING returns no row and the caller reloads instead of overwriting anyone.
            inserted = (await connection.execute(
                insert(submission).values(**db.sql_values(sub)).on_conflict_do_nothing().returning(submission.c.revision))).first()
            if inserted is None:
                raise DuplicateSubmissionKey(s["key"])
            continue
        # an EXISTING revision: only its evaluation state may change, and never once it is done.
        # Zero rows means another process finished it first; the caller reloads and replays.
        mutable = {c: v for c, v in sub.items() if c not in ("attempt_id", "revision", "idempotency_key", "turn", "answer", "visual_answer",
                                                              "hints_seen", "reference_seen", "exposure_sequence", "accepted_at")}
        updated = (await connection.execute(
            update(submission).where(submission.c.attempt_id == values["id"], submission.c.revision == s["revision"],
                                     submission.c.status != "done")
            .values(**db.sql_values(mutable)).returning(submission.c.revision))).first()
        if updated is None:
            raise AlreadyEvaluated(s["revision"])


async def load(connection: AsyncConnection, attempt_id: uuid.UUID, *, user_id: uuid.UUID) -> StoredAttempt | None:
    """The attempt, only if it belongs to `user_id`. Ownership is checked here, always."""
    attempt, submission, question = await db.table("attempt"), await db.table("attempt_submission"), await db.table("question")
    row = (await connection.execute(
        select(attempt, question.c.key.label("question_key")).join(question, question.c.id == attempt.c.question_id)
        .where(attempt.c.id == attempt_id, attempt.c.user_id == user_id))).first()
    if row is None:
        return None
    subs = (await connection.execute(
        select(submission).where(submission.c.attempt_id == attempt_id).order_by(submission.c.revision))).all()
    state = row.engine_state or {}
    practice_row = {
        "id": str(row.id), "question_key": row.question_key, "question_version": row.question_version, "mode": row.mode,
        "practice_language": row.practice_language, "self_confidence_before": row.self_confidence_before,
        "answer": row.answer, "check_result": row.check_result, "evaluation": row.evaluation, "band": row.band,
        "hints_used": row.hints_used, "reference_revealed": row.reference_revealed,
        "revealed_before_submit": row.revealed_before_submit, "follow_up_turns": list(row.follow_up_turns or []),
        "misconceptions_hit": list(row.misconceptions_hit or []), "familiarity": row.familiarity,
        "evidence_mode": state.get("evidence_mode"), "duration_ms": row.duration_ms,
        "tip_turns": state.get("tip_turns") or {}, "next_question": state.get("next_question"),
        "submissions": [{**_submission_dict(s), "evaluating_since": (state.get("evaluating_since") or {}).get(str(s.revision))}
                        for s in subs],
        "exposures": list(row.exposures or []),
    }
    return StoredAttempt(id=row.id, user_id=row.user_id, question_id=row.question_id, question_key=row.question_key,
                         started_at=row.started_at, row=practice_row)


async def started_today(connection: AsyncConnection, user_id: uuid.UUID, *, now: datetime | None = None) -> int:
    """Attempts started since 00:00 UTC today: the daily-allowance count (created_at >= day_start pattern)."""
    attempt = await db.table("attempt")
    now = now or datetime.now(UTC)
    day_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
    return (await connection.execute(
        select(func.count()).select_from(attempt).where(attempt.c.user_id == user_id, attempt.c.started_at >= day_start))).scalar_one()


async def seen_question_ids(connection: AsyncConnection, user_id: uuid.UUID, *, days: int = 30) -> set[uuid.UUID]:
    attempt = await db.table("attempt")
    since = datetime.now(UTC) - timedelta(days=days)
    rows = await connection.execute(
        select(attempt.c.question_id).where(attempt.c.user_id == user_id, attempt.c.started_at >= since).distinct())
    return {row.question_id for row in rows}


async def recent(connection: AsyncConnection, user_id: uuid.UUID, *, limit: int = 20) -> list[dict]:
    """Newest first: what the history page and the plan router need."""
    attempt, question, skill = await db.table("attempt"), await db.table("question"), await db.table("skill")
    rows = (await connection.execute(
        select(attempt.c.id, attempt.c.mode, attempt.c.band, attempt.c.started_at, attempt.c.submitted_at,
               attempt.c.practice_language, attempt.c.hints_used, attempt.c.reference_revealed, question.c.key,
               skill.c.key.label("subject"))
        .join(question, question.c.id == attempt.c.question_id).join(skill, skill.c.id == question.c.subject_id)
        .where(attempt.c.user_id == user_id).order_by(attempt.c.started_at.desc()).limit(limit))).all()
    return [{"id": str(r.id), "question_key": r.key, "subject": r.subject, "mode": r.mode, "band": r.band,
             "started_at": _iso(r.started_at), "submitted_at": _iso(r.submitted_at), "language": r.practice_language,
             "hints_used": r.hints_used, "reference_revealed": r.reference_revealed} for r in rows]


async def band_counts(connection: AsyncConnection, user_id: uuid.UUID) -> dict[str, dict[str, int]]:
    """{subject key: {band: scored answers}} over everything the user has answered."""
    attempt, question, skill = await db.table("attempt"), await db.table("question"), await db.table("skill")
    rows = (await connection.execute(
        select(skill.c.key, attempt.c.band, func.count()).join(question, question.c.id == attempt.c.question_id)
        .join(skill, skill.c.id == question.c.subject_id)
        .where(attempt.c.user_id == user_id, attempt.c.band.is_not(None)).group_by(skill.c.key, attempt.c.band))).all()
    out: dict[str, dict[str, int]] = {}
    for subject, band, n in rows:
        out.setdefault(subject, {})[str(band)] = int(n)
    return out


async def seen_question_keys(connection: AsyncConnection, user_id: uuid.UUID, *, days: int = 30) -> set[str]:
    attempt, question = await db.table("attempt"), await db.table("question")
    since = datetime.now(UTC) - timedelta(days=days)
    rows = await connection.execute(
        select(question.c.key).join(attempt, attempt.c.question_id == question.c.id)
        .where(attempt.c.user_id == user_id, attempt.c.started_at >= since).distinct())
    return {row.key for row in rows}


async def daily_bands(connection: AsyncConnection, user_id: uuid.UUID, *, days: int = 60) -> list[dict]:
    """Scored answers per UTC day, oldest first: {day, STRONG, PARTIAL, WEAK}. The progress graph's input."""
    attempt = await db.table("attempt")
    since = datetime.now(UTC) - timedelta(days=days)
    day = func.date_trunc("day", func.timezone("UTC", attempt.c.started_at)).label("day")   # UTC days whatever the session zone
    rows = (await connection.execute(
        select(day, attempt.c.band, func.count())
        .where(attempt.c.user_id == user_id, attempt.c.band.is_not(None), attempt.c.started_at >= since)
        .group_by(day, attempt.c.band).order_by(day))).all()
    out: dict[str, dict] = {}
    for when, band, n in rows:
        key = when.date().isoformat()
        entry = out.setdefault(key, {"day": key, "STRONG": 0, "PARTIAL": 0, "WEAK": 0})
        entry[str(band)] = entry.get(str(band), 0) + int(n)
    return [out[k] for k in sorted(out)]
