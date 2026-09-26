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
from datetime import date, datetime
from typing import Protocol

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app import db
from app.repo import attempts, events, plans, profiles, questions, sessions, sightings, users
from app.repo.attempts import DuplicateSubmissionKey, StoredAttempt
from app.repo.plans import StoredPlan
from app.repo.profiles import LoadedProfile, StaleProfile
from app.repo.questions import LoadedQuestion, QuestionSummary
from app.repo.sessions import StoredSession
from app.repo.users import Goal
from app.schemas.engine import SkillState

__all__ = ["DuplicateSubmissionKey", "StaleProfile", "Store", "Tx", "DbStore"]


class Tx(Protocol):
    async def validate_answer_images(self, user_id: uuid.UUID, attempt_id: uuid.UUID, images: list) -> bool: ...
    async def load_question(self, *, key: str | None = None, question_id: uuid.UUID | None = None) -> LoadedQuestion | None: ...
    async def list_questions(self, *, language: str, subject: str | None = None) -> list[QuestionSummary]: ...
    # company sightings ("I saw it at X") and the user's goal
    async def sightings_for(self, question_ids: list[str]) -> dict[str, list[dict]]: ...
    async def add_sighting(self, *, question_id: str, user_id: uuid.UUID, company: str) -> str: ...
    async def question_ids_for_company(self, slug: str) -> set[str]: ...
    async def companies(self) -> list[dict]: ...
    async def load_goal(self, user_id: uuid.UUID) -> Goal: ...
    async def save_goal(self, user_id: uuid.UUID, goal: Goal) -> Goal: ...
    async def daily_bands(self, user_id: uuid.UUID) -> list[dict]: ...
    # XP reads (computed on read from stored results; see app.engine.xp)
    async def scored_submissions(self, user_id: uuid.UUID, *, days: int = 365) -> list[dict]: ...
    async def scored_interview_turns(self, user_id: uuid.UUID, *, days: int = 365) -> list[dict]: ...
    # the saved program
    async def load_active_plan(self, user_id: uuid.UUID) -> StoredPlan | None: ...
    async def create_plan(self, *, user_id: uuid.UUID, role_slug: str, seniority: str, week_start: date,
                          minutes_per_day: int, interview_date: date | None, items: list[dict]) -> StoredPlan: ...
    async def deactivate_plan(self, user_id: uuid.UUID) -> None: ...
    async def update_plan_item(self, item_id: uuid.UUID, **fields) -> None: ...
    async def link_attempt_to_plan_item(self, attempt_id: uuid.UUID, item_id: uuid.UUID) -> None: ...
    async def attempt_plan_item(self, attempt_id: uuid.UUID) -> uuid.UUID | None: ...
    async def load_attempt(self, attempt_id: uuid.UUID, *, user_id: uuid.UUID) -> StoredAttempt | None: ...
    async def save_attempt(self, *, user_id: uuid.UUID, question_id: uuid.UUID, row: dict,
                           revisions: set[int] | None = None, known_revisions: int = 0) -> None: ...
    async def save_prose(self, *, user_id: uuid.UUID, question_id: uuid.UUID, row: dict, revision: int) -> bool: ...
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
                           role_slug: str, company_slug: str, expected_revision: int | None = None) -> None: ...
    async def list_sessions(self, user_id: uuid.UUID, *, limit: int = 20) -> list[dict]: ...
    async def sessions_started_today(self, user_id: uuid.UUID) -> int: ...
    async def record_session_metrics(self, *, user_id: uuid.UUID, session_id: uuid.UUID, metrics: list[dict],
                                     seniority: str | None, role_slug: str, company_slug: str) -> int: ...
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

    async def sightings_for(self, question_ids):
        found = await sightings.for_questions(self.connection, [uuid.UUID(str(i)) for i in question_ids])
        return {str(k): v for k, v in found.items()}

    async def add_sighting(self, *, question_id, user_id, company):
        return await sightings.add(self.connection, question_id=uuid.UUID(str(question_id)), user_id=user_id, company=company)

    async def question_ids_for_company(self, slug):
        return {str(i) for i in await sightings.question_ids_for_company(self.connection, slug)}

    async def companies(self):
        return await sightings.companies(self.connection)

    async def load_goal(self, user_id):
        return await users.load_goal(self.connection, user_id)

    async def save_goal(self, user_id, goal):
        return await users.save_goal(self.connection, user_id, goal)

    async def daily_bands(self, user_id):
        return await attempts.daily_bands(self.connection, user_id)

    async def scored_submissions(self, user_id, *, days=365):
        return await attempts.scored_submissions(self.connection, user_id, days=days)

    async def scored_interview_turns(self, user_id, *, days=365):
        return await sessions.scored_turns(self.connection, user_id, days=days)

    async def load_active_plan(self, user_id):
        return await plans.load_active(self.connection, user_id)

    async def create_plan(self, *, user_id, role_slug, seniority, week_start, minutes_per_day, interview_date, items):
        return await plans.create(self.connection, user_id=user_id, role_slug=role_slug, seniority=seniority,
                                  week_start=week_start, minutes_per_day=minutes_per_day, interview_date=interview_date, items=items)

    async def deactivate_plan(self, user_id):
        await plans.deactivate(self.connection, user_id)

    async def update_plan_item(self, item_id, **fields):
        await plans.update_item(self.connection, item_id, **fields)

    async def link_attempt_to_plan_item(self, attempt_id, item_id):
        await plans.link_attempt(self.connection, attempt_id, item_id)

    async def attempt_plan_item(self, attempt_id):
        return await plans.attempt_item(self.connection, attempt_id)

    async def load_attempt(self, attempt_id, *, user_id):
        return await attempts.load(self.connection, attempt_id, user_id=user_id)

    async def save_attempt(self, *, user_id, question_id, row, revisions=None, known_revisions=0):
        await attempts.save(self.connection, user_id=user_id, question_id=question_id, row=row, revisions=revisions,
                            known_revisions=known_revisions)

    async def save_prose(self, *, user_id, question_id, row, revision):
        return await attempts.save_prose(self.connection, user_id=user_id, question_id=question_id, row=row,
                                         revision=revision)

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

    async def save_session(self, *, user_id, row, turns, plan, role_slug, company_slug, expected_revision=None):
        await sessions.save(self.connection, user_id=user_id, row=row, turns=turns, plan=plan,
                            role_slug=role_slug, company_slug=company_slug, expected_revision=expected_revision)

    async def list_sessions(self, user_id, *, limit=20):
        return await sessions.list_sessions(self.connection, user_id, limit=limit)

    async def sessions_started_today(self, user_id):
        return await sessions.started_today(self.connection, user_id)

    async def record_session_metrics(self, *, user_id, session_id, metrics, seniority, role_slug, company_slug):
        return await sessions.record_metrics(self.connection, user_id=user_id, session_id=session_id, metrics=metrics,
                                             seniority=seniority, role_slug=role_slug, company_slug=company_slug)

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
