"""The persistence boundary the practice service talks to.

    Store.transaction()  ->  Tx   one unit of work; commits on exit, rolls back on error

`DbStore` is the real one (Supabase through app.repo). `InMemoryStore` in
memory_store.py follows the same rules and is what the route and service tests use.
Both raise the same exceptions on the two races that matter:

    DuplicateSubmissionKey   another process accepted this idempotency key first
    StaleProfile             another request updated the skill profile first
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Protocol

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app import db
from app.repo import attempts, events, profiles, questions, sessions
from app.repo.attempts import DuplicateSubmissionKey, StoredAttempt
from app.repo.profiles import LoadedProfile, StaleProfile
from app.repo.questions import LoadedQuestion, QuestionSummary
from app.repo.sessions import StoredSession
from app.schemas.engine import SkillState

__all__ = ["DuplicateSubmissionKey", "StaleProfile", "Store", "Tx", "DbStore"]


class Tx(Protocol):
    async def validate_answer_images(self, user_id: uuid.UUID, attempt_id: uuid.UUID, images: list) -> bool: ...
    async def load_question(self, *, key: str | None = None, question_id: uuid.UUID | None = None) -> LoadedQuestion | None: ...
    async def list_questions(self, *, language: str, subject: str | None = None) -> list[QuestionSummary]: ...
    async def load_attempt(self, attempt_id: uuid.UUID, *, user_id: uuid.UUID) -> StoredAttempt | None: ...
    async def save_attempt(self, *, user_id: uuid.UUID, question_id: uuid.UUID, row: dict,
                           revisions: set[int] | None = None, known_revisions: int = 0) -> None: ...
    async def started_today(self, user_id: uuid.UUID, *, now: datetime | None = None) -> int: ...
    async def recent_attempts(self, user_id: uuid.UUID, *, limit: int = 20) -> list[dict]: ...
    async def band_counts(self, user_id: uuid.UUID) -> dict[str, dict[str, int]]: ...
    async def seen_question_keys(self, user_id: uuid.UUID) -> set[str]: ...
    async def load_profile(self, user_id: uuid.UUID) -> LoadedProfile: ...
    async def save_profile(self, loaded: LoadedProfile, states: dict[str, SkillState], *,
                           attempt_id: uuid.UUID | None = None) -> dict[str, int]: ...
    async def user_seniority(self, user_id: uuid.UUID) -> str | None: ...
    async def record_metrics(self, *, user_id: uuid.UUID, attempt_id: uuid.UUID, metrics: list[dict],
                             seniority: str | None) -> int: ...
    async def record_usage(self, *, user_id: uuid.UUID, attempt_id: uuid.UUID, usage_rows: list[dict]) -> int: ...
    async def record_tip(self, *, attempt_id: uuid.UUID, tip_key: str, skill_key: str | None, text: str) -> None: ...
    # mock interviews
    async def load_session(self, session_id: uuid.UUID, *, user_id: uuid.UUID) -> StoredSession | None: ...
    async def save_session(self, *, user_id: uuid.UUID, row: dict, turns: list[dict], plan: list[dict] | None,
                           role_slug: str, company_slug: str) -> None: ...
    async def list_sessions(self, user_id: uuid.UUID, *, limit: int = 20) -> list[dict]: ...
    async def sessions_started_today(self, user_id: uuid.UUID) -> int: ...
    async def record_session_metrics(self, *, user_id: uuid.UUID, session_id: uuid.UUID, metrics: list[dict],
                                     seniority: str | None) -> int: ...
    async def record_session_usage(self, *, user_id: uuid.UUID, session_id: uuid.UUID, usage_rows: list[dict]) -> int: ...


class Store(Protocol):
    def transaction(self) -> AsyncIterator[Tx]: ...


class DbTx:
    def __init__(self, connection: AsyncConnection, *, allow_in_review: bool):
        self.connection = connection
        self.allow_in_review = allow_in_review

    async def validate_answer_images(self, user_id, attempt_id, images):
        prefix = f"{user_id}/{attempt_id}/"
        for image in images:
            if not image.path.startswith(prefix):
                return False
            metadata = (await self.connection.execute(text(
                "select metadata from storage.objects where bucket_id = 'practice-answer-images' and name = :path"),
                {"path": image.path})).scalar_one_or_none()
            if not metadata or metadata.get("mimetype") != image.mime or int(metadata.get("size", 0)) != image.size:
                return False
        return True

    async def load_question(self, *, key=None, question_id=None):
        return await questions.load_question(self.connection, key=key, question_id=question_id,
                                             allow_in_review=self.allow_in_review)

    async def list_questions(self, *, language, subject=None):
        return await questions.list_questions(self.connection, language=language, subject=subject,
                                              allow_in_review=self.allow_in_review)

    async def load_attempt(self, attempt_id, *, user_id):
        return await attempts.load(self.connection, attempt_id, user_id=user_id)

    async def save_attempt(self, *, user_id, question_id, row, revisions=None, known_revisions=0):
        await attempts.save(self.connection, user_id=user_id, question_id=question_id, row=row, revisions=revisions,
                            known_revisions=known_revisions)

    async def started_today(self, user_id, *, now=None):
        return await attempts.started_today(self.connection, user_id, now=now)

    async def recent_attempts(self, user_id, *, limit=20):
        return await attempts.recent(self.connection, user_id, limit=limit)

    async def band_counts(self, user_id):
        return await attempts.band_counts(self.connection, user_id)

    async def seen_question_keys(self, user_id):
        return await attempts.seen_question_keys(self.connection, user_id)

    async def load_profile(self, user_id):
        return await profiles.load(self.connection, user_id)

    async def save_profile(self, loaded, states, *, attempt_id=None):
        return await profiles.save(self.connection, loaded, states, attempt_id=attempt_id)

    async def user_seniority(self, user_id):
        profile = await db.table("user_profile")
        return (await self.connection.execute(
            select(profile.c.seniority_self_assessed).where(profile.c.id == user_id))).scalar_one_or_none()

    async def record_metrics(self, *, user_id, attempt_id, metrics, seniority):
        return await events.record_metrics(self.connection, user_id=user_id, attempt_id=attempt_id, metrics=metrics,
                                           seniority=seniority)

    async def record_usage(self, *, user_id, attempt_id, usage_rows):
        return await events.record_usage(self.connection, user_id=user_id, attempt_id=attempt_id, usage_rows=usage_rows)

    async def load_session(self, session_id, *, user_id):
        return await sessions.load(self.connection, session_id, user_id=user_id)

    async def save_session(self, *, user_id, row, turns, plan, role_slug, company_slug):
        await sessions.save(self.connection, user_id=user_id, row=row, turns=turns, plan=plan,
                            role_slug=role_slug, company_slug=company_slug)

    async def list_sessions(self, user_id, *, limit=20):
        return await sessions.list_sessions(self.connection, user_id, limit=limit)

    async def sessions_started_today(self, user_id):
        return await sessions.started_today(self.connection, user_id)

    async def record_session_metrics(self, *, user_id, session_id, metrics, seniority):
        return await sessions.record_metrics(self.connection, user_id=user_id, session_id=session_id, metrics=metrics,
                                             seniority=seniority)

    async def record_session_usage(self, *, user_id, session_id, usage_rows):
        return await sessions.record_usage(self.connection, user_id=user_id, session_id=session_id, usage_rows=usage_rows)

    async def record_tip(self, *, attempt_id, tip_key, skill_key, text):
        await events.record_tip(self.connection, attempt_id=attempt_id, tip_key=tip_key, skill_key=skill_key, text=text)


class DbStore:
    def __init__(self, engine: AsyncEngine | None = None, *, allow_in_review: bool = False):
        self._engine = engine
        self.allow_in_review = allow_in_review

    @property
    def engine(self) -> AsyncEngine:
        return self._engine or db.get_engine()

    @asynccontextmanager
    async def transaction(self):
        async with self.engine.begin() as connection:
            yield DbTx(connection, allow_in_review=self.allow_in_review)
