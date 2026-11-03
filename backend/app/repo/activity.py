"""Minimal account-owned solved-question events; no answer text leaves this reader."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db


async def solved_question_events(connection: AsyncConnection, user_id: uuid.UUID) -> list[dict]:
    attempt, submission, question = await db.table("attempt"), await db.table("attempt_submission"), await db.table("question")
    practice = (await connection.execute(
        select(submission.c.accepted_at, submission.c.status, submission.c.band, submission.c.flags,
               submission.c.evaluator_model, question.c.key)
        .join(attempt, attempt.c.id == submission.c.attempt_id).join(question, question.c.id == attempt.c.question_id)
        .where(attempt.c.user_id == user_id, submission.c.turn == 0, submission.c.status == "done",
               submission.c.band.is_not(None)))).all()
    out = [{"at": row.accepted_at, "question": row.key, "status": row.status, "band": row.band,
            "flags": list(row.flags or []), "model": row.evaluator_model, "turn": 0} for row in practice]
    session, turn = await db.table("interview_session"), await db.table("session_turn")
    meta = turn.c.question_generation_meta
    interviews = (await connection.execute(
        select(turn.c.session_id, turn.c.turn_index, turn.c.answer_submitted_at,
               question.c.key.label("bank_key"),
               meta["question_key"].astext.label("question_key"), meta["evaluator_model"].astext.label("model"),
               meta["status"].astext.label("status"), meta["band"].astext.label("band"), meta["flags"].label("flags"))
        .join(session, session.c.id == turn.c.session_id).outerjoin(question, question.c.id == turn.c.question_id)
        .where(session.c.user_id == user_id, session.c.status == "completed", turn.c.answer_submitted_at.is_not(None),
               meta["status"].astext == "done", meta["band"].astext.is_not(None)))).all()
    out.extend({"at": row.answer_submitted_at, "question": row.bank_key or row.question_key or f"interview:{row.session_id}:{row.turn_index}",
                "status": row.status, "band": row.band, "flags": list(row.flags or []), "model": row.model, "turn": 0}
               for row in interviews)
    return out
