"""The whole service against the real database, every question, both languages, all failure paths.

Runs only with DATABASE_URL. One connection, one outer transaction for the module, rolled back at
the end; each test runs inside its own savepoint. Nothing survives.
"""

from __future__ import annotations

import asyncio
import time
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app import db
from app.api.errors import ApiError
from app.config import get_settings
from app.engine.catalog import load_catalog
from app.engine.providers import LLMError, LLMRequest, ScriptedProvider
from app.repo import cache
from app.services.practice_service import PracticeService, ServiceConfig
from scripts.seed_db import _seed_in
from tests.livetools import RollbackStore, as_signed_in_user
from tests.test_practice_hardening import CARD, FOLLOW_UP, GOOD, SEEDS, WEAK

pytestmark = pytest.mark.skipif(not get_settings().database_url, reason="DATABASE_URL not set")

SEED_TABLES = ("skill", "skill_dependency", "role_template", "role_skill_set", "company_profile", "company_evidence",
               "company_skill_set", "question", "question_skill", "question_translation", "tips_library", "term_glossary")


def provider_always(evaluation=GOOD, *, evaluator_error: Exception | None = None) -> ScriptedProvider:
    def respond(request: LLMRequest):
        if request.role == "evaluator":
            if evaluator_error is not None:
                raise evaluator_error
            return evaluation
        return {"generator": FOLLOW_UP, "feedback": CARD, "tip": "Next time, try tracing one more input."}[request.role]
    return ScriptedProvider(respond)


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


@pytest_asyncio.fixture
async def case(catalog):
    """One connection and one rolled-back transaction PER TEST (a transaction held open for many
    minutes gets dropped by the pooler). The content is seeded into the transaction first."""
    engine = db.get_engine()
    async with engine.connect() as connection:
        outer = await connection.begin()
        await connection.execute(text("select 1"))                          # BEGIN is on the wire
        tables = {name: await db.table(name) for name in SEED_TABLES}
        started = time.perf_counter()
        cache.clear()
        await _seed_in(connection, tables, catalog)
        cache.clear()
        seed_seconds = time.perf_counter() - started
        user = (await connection.execute(text("select id from public.user_profile limit 1"))).scalar_one()
        email = (await connection.execute(text("select email from auth.users where id = :id"), {"id": user})).scalar_one()
        try:
            yield {"connection": connection, "catalog": catalog, "user_id": user, "email": email,
                   "seed_seconds": seed_seconds}
        finally:
            await outer.rollback()
    await db.dispose()


async def count(connection, sql: str, **params) -> int:
    return (await connection.execute(text(sql), params)).scalar_one()


def service(case, provider, **config) -> PracticeService:
    return PracticeService(RollbackStore(case["connection"]), case["catalog"], provider, ServiceConfig(**config))


class TestEveryQuestion:
    @pytest.mark.parametrize("chunk", [0, 1, 2], ids=["questions 1-10", "questions 11-20", "questions 21-30"])
    async def test_every_question_completes_the_loop_in_english_and_hebrew(self, case, chunk):
        svc = service(case, provider_always(GOOD), daily_attempt_limit=1000)
        user, conn = case["user_id"], case["connection"]
        before = await count(conn, "select count(*) from public.attempt where user_id = :u", u=user)
        today_before = (await svc.progress(user)).attempts_today
        all_keys = [q.key for q in await svc.list_questions(language="en")]
        assert len(all_keys) == 30
        keys = all_keys[chunk * 10:(chunk + 1) * 10]
        problems = []
        for key in keys:
            try:
                he = await svc.get_question(language="he", key=key)
                assert he.language == "he" and any("֐" <= ch <= "׿" for ch in he.prompt), "no Hebrew in prompt"
                view = await svc.start(user, question_key=key, language="en", mode="deep", self_confidence=3)
                attempt_id = uuid.UUID(view.id)
                hints = 0
                while True:
                    hint, view = await svc.next_hint(user, attempt_id)
                    if hint is None:
                        break
                    hints += 1
                assert hints == view.question.hint_count == 3, f"{hints} hints exposed, {view.question.hint_count} declared"
                sub, view = await svc.submit(user, attempt_id, "a careful, correct answer", idempotency_key=f"{key}-main")
                assert sub.status == "done" and sub.band is not None and sub.card is not None, sub.flags
                turns = 0
                while view.pending_follow_up is not None and turns < 3:
                    turn = view.pending_follow_up.turn
                    fsub, view = await svc.submit(user, attempt_id, "and the follow-up answer", idempotency_key=f"{key}-f{turn}",
                                                  follow_up_turn=turn)
                    assert fsub.status == "done"
                    turns += 1
                assert view.status == "done"
                again = await svc.get(user, attempt_id)
                assert again.submission.card == sub.card and len(again.hints) == 3 and again.status == "done"
            except Exception as exc:                       # noqa: BLE001 - collect everything, report once
                problems.append(f"{key}: {type(exc).__name__}: {str(exc)[:300]}")
        assert not problems, "\n".join(problems)

        assert await count(conn, "select count(*) from public.attempt where user_id = :u", u=user) == before + 10
        assert await count(conn, "select count(*) from public.attempt_submission") >= 10
        assert await count(conn, "select count(*) from public.evaluation_metrics where user_id = :u", u=user) >= 10
        assert await count(conn, "select count(*) from public.user_skill_profile where user_id = :u", u=user) >= 3
        bad_scores = await count(conn, "select count(*) from public.user_skill_profile where knowledge_score > 100 or confidence_score > 100")
        assert bad_scores == 0
        progress = await svc.progress(user)
        assert progress.attempts_today == today_before + 10 and len(progress.skills) >= 3
        assert all(s.level is None or 1 <= s.level <= 5 for s in progress.skills)

    async def test_hebrew_attempt_shows_hebrew_hints_and_reference(self, case):
        svc = service(case, provider_always(GOOD))
        view = await svc.start(case["user_id"], question_key="example-sensor-majority", language="he")
        hint, view = await svc.next_hint(case["user_id"], uuid.UUID(view.id))
        assert any("֐" <= ch <= "׿" for ch in hint.text)
        reference, view = await svc.reveal_reference(case["user_id"], uuid.UUID(view.id))
        assert any("֐" <= ch <= "׿" for ch in reference) and view.reference == reference


class TestDurability:
    async def test_restart_and_network_retry_cost_nothing(self, case):
        provider = provider_always(WEAK)
        svc = service(case, provider)
        user, conn = case["user_id"], case["connection"]
        view = await svc.start(user, question_key="example-sensor-majority")
        attempt_id = uuid.UUID(view.id)
        sub, _ = await svc.submit(user, attempt_id, "alarm = A ^ B ^ C", idempotency_key="k1")
        calls, metrics = len(provider.requests), await count(conn, "select count(*) from public.evaluation_metrics")

        restarted = service(case, provider_always(evaluator_error=RuntimeError("no model after restart")))
        again = await restarted.get(user, attempt_id)
        assert again.submission.card == sub.card and again.pending_follow_up.question == sub.follow_up
        replay, _ = await restarted.submit(user, attempt_id, "alarm = A ^ B ^ C", idempotency_key="k1")
        assert replay.replayed and replay.card == sub.card
        assert len(provider.requests) == calls
        assert await count(conn, "select count(*) from public.evaluation_metrics") == metrics
        assert await count(conn, "select count(*) from public.delivered_tip where attempt_id = :a", a=attempt_id) == 1
        assert await count(conn, "select count(*) from public.attempt_submission where attempt_id = :a", a=attempt_id) == 1

    async def test_model_outage_then_retry(self, case):
        svc = service(case, provider_always(evaluator_error=LLMError("provider down", retryable=False)))
        user, conn = case["user_id"], case["connection"]
        view = await svc.start(user, question_key="example-mod-six-counter")
        attempt_id = uuid.UUID(view.id)
        sub, view = await svc.submit(user, attempt_id, "q holds when enable is 0", idempotency_key="k1")
        assert sub.status == "failed" and view.can_retry
        row = (await conn.execute(text("select status, answer from public.attempt_submission where attempt_id = :a"),
                                  {"a": attempt_id})).one()
        assert row.status == "failed" and row.answer == "q holds when enable is 0"
        assert await count(conn, "select count(*) from public.evaluation_metrics where attempt_id = :a", a=attempt_id) == 0

        svc.provider = provider_always(GOOD)
        retried, view = await svc.retry(user, attempt_id)
        assert retried.status == "done" and retried.revision == 1
        assert await count(conn, "select count(*) from public.attempt_submission where attempt_id = :a", a=attempt_id) == 1
        assert await count(conn, "select count(*) from public.evaluation_metrics where attempt_id = :a", a=attempt_id) >= 1

    async def test_simultaneous_double_clicks_score_once(self, case):
        provider = provider_always(GOOD)
        svc = service(case, provider)
        user, conn = case["user_id"], case["connection"]
        view = await svc.start(user, question_key="example-sensor-majority")
        attempt_id = uuid.UUID(view.id)
        results = await asyncio.gather(*[svc.submit(user, attempt_id, "alarm = (A&B)|(A&C)|(B&C)", idempotency_key="dup")
                                         for _ in range(3)])
        assert sum(1 for sub, _ in results if not sub.replayed) == 1
        assert sum(1 for r in provider.requests if r.role == "evaluator") == 1
        assert await count(conn, "select count(*) from public.attempt_submission where attempt_id = :a", a=attempt_id) == 1

    async def test_daily_limit_counts_real_rows(self, case):
        user = case["user_id"]
        today_before = (await service(case, provider_always(GOOD)).progress(user)).attempts_today
        svc = service(case, provider_always(GOOD), daily_attempt_limit=today_before + 2)
        await svc.start(user, question_key="example-sensor-majority")
        await svc.start(user, question_key="example-nand-only-enable")
        with pytest.raises(ApiError) as raised:
            await svc.start(user, question_key="example-masked-equality")
        assert raised.value.code == "usage_limit"
        assert (await svc.progress(user)).attempts_today == today_before + 2


class TestAccessBoundaries:
    async def test_another_user_cannot_see_or_touch_the_attempt(self, case):
        svc = service(case, provider_always(GOOD))
        view = await svc.start(case["user_id"], question_key="example-sensor-majority")
        stranger = uuid.uuid4()
        for call in (svc.get(stranger, uuid.UUID(view.id)),
                     svc.submit(stranger, uuid.UUID(view.id), "x", idempotency_key="k"),
                     svc.next_hint(stranger, uuid.UUID(view.id)),
                     svc.reveal_reference(stranger, uuid.UUID(view.id))):
            with pytest.raises(ApiError) as raised:
                await call
            assert raised.value.code == "not_found"

    async def test_rls_lets_a_user_read_their_result_but_never_the_internals(self, case):
        svc = service(case, provider_always(WEAK))
        user, conn, email = case["user_id"], case["connection"], case["email"]
        view = await svc.start(user, question_key="example-sensor-majority")
        attempt_id = uuid.UUID(view.id)
        await svc.submit(user, attempt_id, "alarm = A ^ B ^ C", idempotency_key="k1")

        async with as_signed_in_user(conn, user, email):
            own = await count(conn, "select count(*) from public.attempt where id = :a", a=attempt_id)
            card = (await conn.execute(text("select card, band, status from public.attempt_submission where attempt_id = :a"),
                                       {"a": attempt_id})).one()
            assert own == 1 and card.status == "done" and card.card is not None and card.band == "WEAK"
            level = (await conn.execute(text("select proficiency_level, trend from public.user_skill_profile where user_id = :u"),
                                        {"u": user})).all()
            assert level
            for forbidden in ("select evaluation from public.attempt_submission",
                              "select evidence_weight from public.attempt_submission",
                              "select knowledge_score from public.user_skill_profile",
                              "select engine_state from public.user_skill_profile",
                              "select engine_state from public.attempt",
                              "select knowledge_score_after from public.evaluation_metrics"):
                nested = await conn.begin_nested()
                with pytest.raises(Exception, match="permission denied"):
                    await conn.execute(text(forbidden))
                await nested.rollback()

        async with as_signed_in_user(conn, uuid.uuid4(), "someone-else@example.com"):
            assert await count(conn, "select count(*) from public.attempt") == 0
            assert await count(conn, "select count(*) from public.attempt_submission") == 0
            assert await count(conn, "select count(*) from public.user_skill_profile") == 0
            assert await count(conn, "select count(*) from public.question") == 0     # not a member: no questions at all


class TestContentAndSpeed:
    async def test_seeding_again_keeps_ids_and_review_state(self, case):
        conn, catalog = case["connection"], case["catalog"]
        before = dict((await conn.execute(text("select key, id from public.question"))).all())
        # publishing needs a reviewer, a date and a settled reuse status (question_publish_* checks)
        await conn.execute(text("update public.question set status = 'published', reviewed_by = 'harel', reviewed_at = now(), "
                                "reuse_status = 'permitted' where key = 'example-sensor-majority'"))
        tables = {name: await db.table(name) for name in SEED_TABLES}
        await _seed_in(conn, tables, catalog)
        after = dict((await conn.execute(text("select key, id from public.question"))).all())
        assert after == before, "question ids changed: Harel's app references them"
        row = (await conn.execute(text("select status, reviewed_by from public.question where key = 'example-sensor-majority'"))).one()
        assert row.status == "published" and row.reviewed_by == "harel"
        assert await count(conn, "select count(*) from public.question_skill") == sum(len(q.skills) for q in catalog.questions.values())

    async def test_listing_and_loading_are_fast_enough_for_a_page(self, case):
        svc = service(case, provider_always(GOOD))
        started = time.perf_counter()
        listing = await svc.list_questions(language="en")
        list_seconds = time.perf_counter() - started
        started = time.perf_counter()
        await svc.get_question(language="en", key=listing[0].key)
        one_seconds = time.perf_counter() - started
        print(f"\nlist_questions: {list_seconds:.2f}s for {len(listing)} | get_question: {one_seconds:.2f}s | "
              f"seed: {case['seed_seconds']:.0f}s")
        assert list_seconds < 3.0, f"listing 30 questions took {list_seconds:.1f}s"
        assert one_seconds < 2.0


class TestOverHttp:
    async def test_the_http_flow_against_the_real_database(self, case):
        """The FastAPI app with DbStore, a token for the real pilot user, the real access resolver."""
        from httpx import ASGITransport, AsyncClient

        from app.main import app
        from app.runtime import build_runtime
        from tests.authtools import make_token, make_verifier

        settings = get_settings()
        app.state.verifier = make_verifier()
        app.state.access_resolver = None                                   # the real one: jr_members + user_profile
        app.state.runtime = build_runtime(settings, catalog=case["catalog"], provider=provider_always(WEAK),
                                          store=RollbackStore(case["connection"]))
        _, token = make_token(case["user_id"], email=case["email"])
        h = {"Authorization": f"Bearer {token}"}
        base = "/v1/practice/attempts"
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                me = (await client.get("/v1/me", headers=h)).json()
                assert me["pilot_member"] is True and me["id"] == str(case["user_id"])
                assert len((await client.get("/v1/questions", headers=h)).json()) == 30
                attempt = (await client.post(base, json={"question_key": "example-sensor-majority", "language": "he"}, headers=h)).json()
                aid = attempt["id"]
                hint = (await client.post(f"{base}/{aid}/hints/next", headers=h)).json()["hint"]
                assert any("\u0590" <= ch <= "\u05ff" for ch in hint["text"])
                response = await client.post(f"{base}/{aid}/submissions", json={"answer": "alarm = A ^ B ^ C"},
                                             headers={**h, "Idempotency-Key": "http-1"})
                assert response.status_code == 200, response.text
                sub = response.json()["submission"]
                assert sub["status"] == "done" and sub["band"] == "WEAK" and sub["card"] and sub["follow_up"]
                replay = await client.post(f"{base}/{aid}/submissions", json={"answer": "alarm = A ^ B ^ C"},
                                           headers={**h, "Idempotency-Key": "http-1"})
                assert replay.json()["submission"]["replayed"] is True
                again = (await client.get(f"{base}/{aid}", headers=h)).json()
                assert again["submission"]["card"] == sub["card"] and again["pending_follow_up"] is not None
                progress = (await client.get("/v1/me/progress", headers=h)).json()
                assert progress["attempts_today"] >= 1 and progress["skills"]
                # a token whose user no longer exists in Auth: 401, never a 500 from the profile foreign key
                _, ghost = make_token(email="nobody@example.com")
                response = await client.get(f"{base}/{aid}", headers={"Authorization": f"Bearer {ghost}"})
                assert response.status_code == 401 and response.json()["error"]["code"] == "unauthenticated"
                # a real account that is not on the pilot list: 403
                _, stranger = make_token(case["user_id"], email="not-a-member@example.com")
                assert (await client.get(f"{base}/{aid}", headers={"Authorization": f"Bearer {stranger}"})).status_code == 403
            assert await count(case["connection"], "select count(*) from public.attempt_submission where attempt_id = :a", a=aid) == 1
        finally:
            for name in ("verifier", "access_resolver", "runtime"):
                if hasattr(app.state, name):
                    delattr(app.state, name)
