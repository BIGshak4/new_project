"""Regression tests for the night check of 18–19 October 2026 (the concurrency reviewer's findings)."""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import UTC, datetime

import pytest

from app import main
from app.engine import scores
from app.engine.catalog import load_catalog
from app.repo.cache import TTLCache
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from tests.conftest import make_evaluation
from tests.test_interview_service import Clock, interviewer
from tests.test_practice_hardening import SEEDS

USER = uuid.uuid4()


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def respond_ok(scope, receive, send):
    raise AssertionError("the limiter should not reach the app in these tests")


class TestTheLimiterEvictsExpiredBucketsFirst:
    def test_a_churning_caller_cannot_flush_a_live_callers_count(self, monkeypatch):
        """Review finding 2026-10-19: pure LRU let 10,000 rotated identities erase every other caller's window."""
        monkeypatch.setattr(main, "MAX_RATE_LIMIT_BUCKETS", 50, raising=False)
        monkeypatch.setattr(main, "RATE_LIMIT_PER_MINUTE", 3, raising=False)
        limiter = main.StreamLimits(respond_ok)
        for _ in range(3):
            assert not limiter._over_limit("a:9.9.9.9")
        assert limiter._over_limit("a:9.9.9.9")                                   # at its limit
        for index in range(500):                                                   # a churner with fresh identities
            limiter._over_limit(f"t:{index:016x}")
        assert len(limiter._buckets) <= 50
        assert limiter._over_limit("a:9.9.9.9"), "the live caller's window was flushed by the churn"

    def test_expired_buckets_go_before_live_ones(self, monkeypatch):
        monkeypatch.setattr(main, "MAX_RATE_LIMIT_BUCKETS", 3, raising=False)
        limiter = main.StreamLimits(respond_ok)
        limiter._over_limit("a:live")
        limiter._buckets["a:stale-1"] = main.deque([time.monotonic() - 120])
        limiter._buckets["a:stale-2"] = main.deque([time.monotonic() - 120])
        limiter._buckets.move_to_end("a:live")                                     # live is the most recent
        limiter._buckets.move_to_end("a:stale-1", last=False)                      # stale-1 is the least recent
        limiter._over_limit("a:new")                                               # the 4th bucket forces an eviction
        assert "a:live" in limiter._buckets and "a:new" in limiter._buckets
        assert not ({"a:stale-1", "a:stale-2"} <= set(limiter._buckets))


class TestTheCacheHonoursAnInvalidationDuringALoad:
    async def test_a_value_loaded_before_the_invalidation_is_served_but_not_kept(self):
        cache: TTLCache[str] = TTLCache(seconds=60)
        started = asyncio.Event()

        async def slow_old():
            started.set()
            await asyncio.sleep(0.02)
            return "old"

        task = asyncio.create_task(cache.get("k", slow_old))
        await started.wait()
        cache.invalidate("k")                                                      # a member added mid-load
        assert await task == "old"                                                 # the caller gets what it loaded
        assert cache.peek("k") is None                                             # but the cache does not keep it

        async def fresh():
            return "new"
        assert await cache.get("k", fresh) == "new"


class TestSupersededRevisionsNeverCount:
    async def test_the_xp_and_soft_skill_readers_skip_superseded_revisions(self, catalog):
        store = InMemoryStore(catalog)
        now = datetime.now(UTC).isoformat()
        evaluation = make_evaluation(correctness=0.9, depth=0.8).model_dump(mode="json")
        store.attempts[uuid.uuid4()] = {
            "user_id": USER, "started_at": now, "row": {"question_key": "example-sensor-majority", "submissions": [
                {"status": "done", "band": "STRONG", "accepted_at": now, "turn": 0, "revision": 1, "flags": ["superseded"],
                 "evaluation": evaluation, "hints_seen": 0, "reference_seen": False},
                {"status": "done", "band": "STRONG", "accepted_at": now, "turn": 0, "revision": 2, "flags": [],
                 "evaluation": evaluation, "hints_seen": 0, "reference_seen": False},
            ]}}
        async with store.transaction() as tx:
            assert len(await tx.scored_submissions(USER)) == 1
            assert len(await tx.soft_skill_evidence(USER)) == 1


class TestTheInterviewRecordsRelatednessConsistently:
    async def test_off_topic_reaches_the_metrics_row_and_is_judged_on_the_raw_evaluation(self, catalog):
        off_topic = make_evaluation(correctness=0.05, depth=0.1, key_points_hit=[],
                                    behavior_signals=["answered_different_question"]).model_dump()
        store = InMemoryStore(catalog)
        svc = InterviewService(store, catalog, interviewer([off_topic]), InterviewConfig(reviewed_only=False))
        svc.clock = Clock()
        view = await svc.start(USER, duration_min=20, language="en")
        sid = uuid.UUID(view.id)
        svc.clock.advance()
        await svc.answer(USER, sid, view.current_turn.index, "a story about my weekend", idempotency_key="t0")
        session = store.sessions[sid]
        turn = session["turns"][0]
        assert scores.OFF_TOPIC_FLAG in (turn["question_generation_meta"].get("flags") or [])
        assert scores.OFF_TOPIC_FLAG in (session["row"]["state"]["metrics"][0].get("eval_flags") or [])


class TestTheLimiterKeysOnTheCredential:
    def test_one_token_in_three_spellings_is_one_bucket(self):
        limiter = main.StreamLimits(respond_ok)
        def scope(*headers):
            return {"type": "http", "headers": list(headers), "client": ("1.2.3.4", 1)}
        a = limiter._caller(scope((b"authorization", b"Bearer abc.def")))
        b = limiter._caller(scope((b"authorization", b"bearer abc.def")))
        c = limiter._caller(scope((b"Authorization", b"  Bearer abc.def  ")))
        assert a == b == c and a.startswith("t:")
        assert limiter._caller(scope((b"authorization", b"Bearer other"))) != a
        first = limiter._caller(scope((b"authorization", b"Bearer abc.def"), (b"authorization", b"Bearer rotating")))
        assert first == a                                                           # the first header, as the authenticator reads it
        assert limiter._caller(scope()) == "a:1.2.3.4"


class TestHealthDetailNeedsAKeyWhenOneIsSet:
    def test_the_rule(self):
        from types import SimpleNamespace
        assert main.health_detail_allowed(SimpleNamespace(health_key=None), None) is True
        assert main.health_detail_allowed(SimpleNamespace(health_key="k"), None) is False
        assert main.health_detail_allowed(SimpleNamespace(health_key="k"), "wrong") is False
        assert main.health_detail_allowed(SimpleNamespace(health_key="k"), "k") is True


class TestSoftSkillEdges:
    def test_a_judged_skill_outside_the_plan_does_not_crash_the_overall_word(self):
        from app.engine import soft_skills as ss
        hard = {"ghost": {"levels": 12, "span_days": 30, "gradient": 12.0, "improvement": "improving_quickly",
                          "slope_per_week": 3.0, "improvement_per_week": "improving"}}
        assert ss.overall_improvement([], hard, {"other": 1.0})["improvement"] == "too_early"
        assert ss.overall_improvement([], hard, {"ghost": 0.05})["improvement"] == "improving_quickly"

    def test_the_windows_are_strict_like_the_expiry(self):
        from datetime import timedelta

        from app.engine import soft_skills as ss
        now = datetime(2026, 10, 19, 12, tzinfo=UTC)
        def ev(days_ago):
            return ss.Evidence(at=now - timedelta(days=days_ago), evaluation={"clarity": 0.6, "correctness": 0.6, "depth": 0.5},
                               flags=[], archetype="conceptual", primary_skill="counters")
        just_out = next(x for x in ss.assess([ev(49.5)] * 5, now) if x.key == "clear_communication")
        just_in = next(x for x in ss.assess([ev(48.5)] * 5, now) if x.key == "clear_communication")
        assert just_out.answers == 0 and just_out.level is None
        assert just_in.answers == 5 and just_in.level is not None
        old = next(x for x in ss.assess([ev(100 + i) for i in range(12)], now) if x.key == "clear_communication")
        assert old.answers == 0 and old.gradient_answers == 12                      # the word rests on the gradient count
        assert ss.LEVEL_WINDOW_DAYS == 49

    def test_a_none_flags_list_is_fine(self):
        from tests.conftest import make_evaluation
        assert scores.related_to_question(make_evaluation(), flags=None) is True
        assert scores.related_to_question(None, flags=None) is True


class TestTheInterviewHidesTheVerdictUntilRevealed:
    async def test_related_and_the_flag_appear_only_with_the_results(self, catalog):
        off_topic = make_evaluation(correctness=0.05, depth=0.1, key_points_hit=[],
                                    behavior_signals=["answered_different_question"]).model_dump()
        good = make_evaluation(correctness=0.9, depth=0.8).model_dump()
        store = InMemoryStore(catalog)
        svc = InterviewService(store, catalog, interviewer([off_topic, good]), InterviewConfig(reviewed_only=False))
        svc.clock = Clock()
        view = await svc.start(USER, duration_min=20, language="en")
        sid = uuid.UUID(view.id)
        svc.clock.advance()
        _, after = await svc.answer(USER, sid, view.current_turn.index, "my weekend", idempotency_key="t0")
        first = after.turns[0]
        if after.status == "in_progress":
            assert first.related is True and scores.OFF_TOPIC_FLAG not in first.flags   # hidden with the band
        from tests.test_interview_service import run_to_the_end
        done, _ = await run_to_the_end(svc, USER, after)
        assert done.status == "completed"
        assert done.turns[0].related is False and scores.OFF_TOPIC_FLAG in done.turns[0].flags
