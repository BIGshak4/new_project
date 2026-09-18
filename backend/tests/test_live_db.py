"""The real repository against the real database, inside one transaction that is always rolled back.

Runs only when backend/.env has DATABASE_URL. The content is seeded into the same
transaction first (the live bank is not enriched until stage G), so the test never
depends on, or changes, what is in the database.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app import db
from app.config import get_settings
from app.engine.catalog import load_catalog
from app.engine.practice import PracticeAttempt, PracticeContext
from app.repo import cache
from app.repo.attempts import DuplicateSubmissionKey
from app.repo.profiles import StaleProfile
from app.services.store import DbTx
from scripts.seed_db import _seed_in
from tests.test_practice_hardening import GOOD, SEEDS, WEAK, scripted

pytestmark = pytest.mark.skipif(not get_settings().database_url, reason="DATABASE_URL not set")
Q = "example-sensor-majority"


@pytest.fixture
async def tx():
    """A DbTx on a connection whose transaction is opened before any statement and rolled back after."""
    engine = db.get_engine()
    async with engine.connect() as connection:
        transaction = await connection.begin()
        await connection.execute(text("select 1"))                 # the BEGIN is on the wire from here on
        catalog = load_catalog(SEEDS)
        tables = {name: await db.table(name) for name in
                  ("skill", "skill_dependency", "role_template", "role_skill_set", "company_profile", "company_evidence",
                   "company_skill_set", "question", "question_skill", "question_translation", "tips_library",
                   "term_glossary")}
        cache.clear()
        await _seed_in(connection, tables, catalog)
        cache.clear()
        user_id = (await connection.execute(text("select id from public.user_profile limit 1"))).scalar_one()
        try:
            yield DbTx(connection, allow_in_review=True), catalog, user_id
        finally:
            await transaction.rollback()
            await connection.execute(text("select 1"))
    await db.dispose()


def context(catalog, provider) -> PracticeContext:
    return PracticeContext(provider=provider, skills=catalog.leaf_skills, language="en", seniority="student",
                           difficulty_ceiling=5, required_levels={k: 2 for k in catalog.leaf_skills},
                           tips=list(catalog.tips.values()), polish_tips=False)


class TestLiveRepository:
    async def test_questions_round_trip_from_the_database(self, tx):
        store, catalog, _ = tx
        listing = await store.list_questions(language="he")
        assert len(listing) == 30 and all(q.language == "he" for q in listing)
        loaded = await store.load_question(key=Q)
        seed = catalog.questions[Q]
        assert loaded.question.primary_skill == seed.primary_skill
        assert loaded.question.deterministic_check == seed.deterministic_check
        assert [c.key for c in loaded.question.rubric] == [c.key for c in seed.rubric]
        assert {e.key: e.tip_key for e in loaded.question.common_errors} == {e.key: e.tip_key for e in seed.common_errors}
        assert loaded.question.text("he").hints == seed.text("he").hints
        assert loaded.question.text("en").reference_solution == seed.text("en").reference_solution
        assert loaded.question.archetype == seed.archetype and "archetype" not in loaded.question.assets

    async def test_attempt_and_profile_round_trip(self, tx):
        store, catalog, user_id = tx
        loaded = await store.load_question(key=Q)
        profile = await store.load_profile(user_id)
        attempt = PracticeAttempt(context(catalog, scripted([WEAK])), loaded.question, profile.states)
        attempt.next_hint()
        outcome = await attempt.submit("alarm = A ^ B ^ C", idempotency_key="k1")
        assert outcome.status.value == "done"

        await store.save_attempt(user_id=user_id, question_id=loaded.id, row=attempt.attempt_row())
        versions = await store.save_profile(profile, attempt.skill_states, attempt_id=attempt.attempt_id_uuid)
        assert set(versions) >= {loaded.question.primary_skill} and all(v == 1 for v in versions.values())
        n = await store.record_metrics(user_id=user_id, attempt_id=attempt.attempt_id_uuid, metrics=outcome.metrics,
                                       seniority="student")
        assert n == len(outcome.metrics)
        await store.record_usage(user_id=user_id, attempt_id=attempt.attempt_id_uuid,
                                 usage_rows=[u.as_row("deep") for u in outcome.usage])
        await store.record_tip(attempt_id=attempt.attempt_id_uuid, tip_key=outcome.tip_key,
                               skill_key=loaded.question.primary_skill, text=outcome.tip_text)

        # back from the database, as a restart would see it
        stored = await store.load_attempt(attempt.attempt_id_uuid, user_id=user_id)
        again = await store.load_profile(user_id)
        restored = PracticeAttempt.restore(context(catalog, scripted([])), loaded.question, again.states, stored.row)
        assert restored.main_submission.card == outcome.submission.card
        assert restored.pending_follow_up["question"] == outcome.follow_up and restored.hints_used == attempt.hints_used == 2
        assert again.versions[loaded.question.primary_skill] == 1
        assert again.states[loaded.question.primary_skill].turns == 1
        assert await store.load_attempt(attempt.attempt_id_uuid, user_id=uuid.uuid4()) is None     # someone else

        # the database refuses a second revision with the same key, and a stale profile write
        stored.row["submissions"].append({**stored.row["submissions"][0], "revision": 2})
        with pytest.raises(DuplicateSubmissionKey):
            await store.save_attempt(user_id=user_id, question_id=loaded.id, row=stored.row)
        with pytest.raises(StaleProfile):
            await store.save_profile(profile, attempt.skill_states, attempt_id=attempt.attempt_id_uuid)   # old versions
        await store.save_profile(again, again.states, attempt_id=attempt.attempt_id_uuid)             # fresh ones
        assert (await store.load_profile(user_id)).versions[loaded.question.primary_skill] == 2

    async def test_second_attempt_scores_on_top_of_the_saved_profile(self, tx):
        store, catalog, user_id = tx
        loaded = await store.load_question(key=Q)
        for answer, reply in (("alarm = A ^ B ^ C", WEAK), ("alarm = (A&B)|(A&C)|(B&C)", GOOD)):
            profile = await store.load_profile(user_id)
            attempt = PracticeAttempt(context(catalog, scripted([reply])), loaded.question, profile.states)
            await attempt.submit(answer)
            await store.save_attempt(user_id=user_id, question_id=loaded.id, row=attempt.attempt_row())
            await store.save_profile(profile, attempt.skill_states, attempt_id=attempt.attempt_id_uuid)
        final = await store.load_profile(user_id)
        assert final.states[loaded.question.primary_skill].turns == 2
        assert await store.started_today(user_id) >= 2
        assert [r["question_key"] for r in await store.recent_attempts(user_id, limit=2)] == [Q, Q]
