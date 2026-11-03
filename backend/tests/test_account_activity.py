"""Account-owned solved-question days, independent of grades, XP and duplicate revisions."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.engine.activity import activity_summary
from app.engine.catalog import load_catalog
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_goal_jobtypes_sightings import client, headers  # noqa: F401 -- memory-backed HTTP fixtures
from tests.test_practice_hardening import GOOD, SEEDS, scripted


def event(at="2026-11-03T08:00:00+00:00", question="q1", **updates):
    return {"at": at, "question": question, "status": "done", "band": "WEAK", "model": "real-evaluator",
            "flags": ["off_topic"], "turn": 0, **updates}


NOW = datetime(2026, 11, 3, 12, tzinfo=UTC)


def test_zero_xp_answers_count_once_per_question_and_day_without_counting_open_or_demo_work():
    events = [event(), event(), event(question="q2"), event(question="follow", turn=1),
              event(question="demo", model="scripted"), event(question="pending", status="evaluating"),
              event(question="failed", status="failed"), event(question="skipped", status="skipped"),
              event(question="old", flags=["superseded"]), event(question="review", flags=["content_review_pending"])]
    result = activity_summary(events, now=NOW)
    assert result["streak_days"] == 1 and result["today_count"] == 2
    assert result["days"] == [{"date": "2026-11-03", "questions": 2}]


def test_streak_uses_local_submission_calendar_days_and_allows_today_to_be_unfinished():
    events = [event("2026-11-01T12:00:00+00:00"), event("2026-11-01T22:30:00+00:00"),
              event("2026-11-02T22:30:00+00:00")]
    local = activity_summary(events, "Asia/Jerusalem", now=NOW)
    assert local["timezone"] == "Asia/Jerusalem" and local["streak_days"] == 3 and local["today_count"] == 1
    utc = activity_summary(events, "UTC", now=NOW)
    assert utc["streak_days"] == 2 and utc["today_count"] == 0
    assert activity_summary(events, "Asia/Jerusalem", now=NOW + timedelta(days=2))["streak_days"] == 0


def test_dst_boundary_counts_one_local_day_and_invalid_zones_safely_fall_back_to_utc():
    events = [event("2026-11-01T05:30:00+00:00"), event("2026-11-01T06:30:00+00:00")]
    result = activity_summary(events, "America/New_York", now=NOW)
    assert result["days"] == [{"date": "2026-11-01", "questions": 1}]
    assert activity_summary(events, "../../bad", now=NOW)["timezone"] == "UTC"
    assert activity_summary([], "Unknown/Unknown", now=NOW)["today_count"] == 0


def test_absent_invalid_or_future_dates_cannot_create_activity():
    result = activity_summary([event(at=None), event(at="not a date"), event(at="2026-11-05T00:00:00Z")], now=NOW)
    assert result["streak_days"] == 0 and result["last_solved_date"] is None and result["days"] == []


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


async def test_memory_reader_isolates_accounts_and_counts_completed_interview_questions(catalog):
    store = InMemoryStore(catalog)
    service = PracticeService(store, catalog, scripted([GOOD]), ServiceConfig(suggest_reviewed_only=False))
    user, other = uuid.uuid4(), uuid.uuid4()
    stamp = datetime.now(UTC).isoformat()
    store.attempts[uuid.uuid4()] = {"user_id": user, "row": {"question_key": "q1", "submissions": [
        {"accepted_at": stamp, "status": "done", "band": "WEAK", "evaluator_model": "real", "turn": 0,
         "flags": ["off_topic"]},
        {"accepted_at": stamp, "status": "done", "band": "WEAK", "evaluator_model": "real", "turn": 0}]}}
    store.attempts[uuid.uuid4()] = {"user_id": other, "row": {"question_key": "private", "submissions": [
        {"accepted_at": stamp, "status": "done", "band": "STRONG", "evaluator_model": "real", "turn": 0}]}}
    for status in ("running", "completed"):
        store.sessions[uuid.uuid4()] = {"user_id": user, "row": {"status": status}, "turns": [
            {"turn_index": 0, "question_key": "interview-q", "answer_submitted_at": stamp,
             "question_generation_meta": {"status": "done", "band": "PARTIAL", "evaluator_model": "real"}}]}
    result = await service.activity(user)
    assert result["today_count"] == 2 and result["streak_days"] == 1
    assert (await service.activity(other))["today_count"] == 1
    assert (await service.activity(uuid.uuid4()))["days"] == []


async def test_complete_exploration_has_distinct_real_recommendations_without_role_readiness_claim(catalog):
    store = InMemoryStore(catalog)
    service = PracticeService(store, catalog, scripted([GOOD]), ServiceConfig(suggest_reviewed_only=False))
    user = uuid.uuid4()
    await service.save_goal(user, job_type=None, job_types=[], learning_mode="explore", interview_date=None,
                            minutes_per_day=30, seniority="student", language="he")
    result = await service.readiness(user, language="he")
    assert result.next_questions and len({q.key for q in result.next_questions}) == len(result.next_questions)
    assert all(q.key in catalog.questions and q.title == catalog.questions[q.key].text("he").title
               for q in result.next_questions)
    assert result.job_type is None and not result.ready_to_judge
    assert result.readiness_score is None and result.readiness_word is None


async def test_activity_http_reads_only_the_authenticated_account(client, headers):  # noqa: F811 -- imported pytest fixtures
    from app.main import app

    identity = (await client.get("/v1/me", headers=headers)).json()
    user, other = uuid.UUID(identity["id"]), uuid.uuid4()
    store = app.state.runtime.store
    for owner, key in ((user, "mine"), (other, "private")):
        store.attempts[uuid.uuid4()] = {"user_id": owner, "row": {"question_key": key, "submissions": [
            {"accepted_at": datetime.now(UTC).isoformat(), "status": "done", "band": "WEAK",
             "evaluator_model": "real", "turn": 0, "flags": ["off_topic"]}]}}
    response = await client.get("/v1/me/activity?timezone=Asia%2FJerusalem", headers=headers)
    assert response.status_code == 200
    assert response.json()["today_count"] == 1 and response.json()["timezone"] == "Asia/Jerusalem"
    assert "private" not in response.text and "mine" not in response.text
    assert (await client.get("/v1/me/activity")).status_code == 401
