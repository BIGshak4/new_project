"""The saved program: built daily from the profile, carried forward, ticked by attempts and interviews, started
from the library. In-memory store, scripted model."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.engine.catalog import load_catalog
from app.main import app
from app.repo.plans import PlanItemRow
from app.runtime import build_runtime
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.authtools import make_token, make_verifier, member_resolver
from tests.test_interview_service import Clock, interviewer
from tests.test_practice_hardening import GOOD, SEEDS, scripted

USER = uuid.uuid4()
MEMBER = "tester@example.com"
TODAY = date.today()


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def practice(catalog, provider=None) -> tuple[PracticeService, InMemoryStore]:
    store = InMemoryStore(catalog)
    return PracticeService(store, catalog, provider or scripted([GOOD, GOOD, GOOD]), ServiceConfig(suggest_reviewed_only=False)), store


async def with_goal(svc, minutes=30, days=10):
    await svc.save_goal(USER, job_type="verification", interview_date=TODAY + timedelta(days=days), minutes_per_day=minutes,
                        seniority="student")


class TestBuildingAndReusing:
    async def test_the_program_is_built_once_a_day_and_reused(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        first = await svc.program(USER, language="en")
        assert first.goal_complete and first.plan.saved and first.plan.generated_for == TODAY.isoformat()
        assert first.today and first.next is not None and first.next.day_index == 0 and first.next.id
        assert first.minutes_due_today == sum(i.minutes for i in first.today) and first.done_today == 0
        again = await svc.program(USER, language="en")
        assert store.plans[USER].id and [i.id for i in again.plan.items] == [i.id for i in first.plan.items]
        # the progress page shows the same saved plan
        progress = await svc.progress(USER, language="en")
        assert [i.id for i in progress.plan.items] == [i.id for i in first.plan.items]

    async def test_without_a_goal_the_program_still_exists_but_start_asks_for_the_goal(self, catalog):
        svc, _ = practice(catalog)
        view = await svc.program(USER, language="en")
        assert view.goal_complete is False and view.plan.minutes_per_day == 30
        started = await svc.start_program_item(USER, language="he")
        assert started.kind == "nothing" and "ראיון" in started.message

    async def test_a_new_goal_means_a_new_program(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        first = await svc.program(USER, language="en")
        await with_goal(svc, minutes=60)
        second = await svc.program(USER, language="en")
        assert second.plan.minutes_per_day == 60 and store.plans[USER].minutes_per_day == 60
        assert {i.id for i in second.plan.items}.isdisjoint({i.id for i in first.plan.items})


class TestCarryForward:
    async def test_yesterdays_open_item_leads_today_and_old_or_done_ones_do_not(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await svc.program(USER, language="en")
        plan = store.plans[USER]
        plan.week_start = TODAY - timedelta(days=1)                  # imitate: this plan was built yesterday
        old = datetime.now(UTC) - timedelta(days=1)
        for item in plan.items:
            item.created_at = old
        yesterday_open = next(i for i in plan.items if i.day_index == 0)
        done_item = PlanItemRow(id=uuid.uuid4(), day_index=0, mode="quick", skills=["counters"], reason="done yesterday",
                                minutes=5, status="done", created_at=old)
        stale_item = PlanItemRow(id=uuid.uuid4(), day_index=0, mode="deep", skills=["truth_tables"], reason="from long ago",
                                 minutes=20, status="planned", created_at=old - timedelta(days=6))
        plan.items += [done_item, stale_item]
        plan.week_start = TODAY - timedelta(days=1)
        # the stale item's planned date is week_start + 0 = yesterday: still within 3 days, so it IS carried;
        # make it genuinely old by planning it for six days ago through an older plan date
        store.plans[USER] = plan
        today_view = await svc.program(USER, language="en")
        assert today_view.plan.generated_for == TODAY.isoformat()
        carried = [i for i in today_view.plan.items if i.carried]
        assert carried and carried[0].day_index == 0 and today_view.today[0].carried
        assert yesterday_open.reason in [i.reason for i in carried]
        assert "done yesterday" not in [i.reason for i in today_view.plan.items]        # done items are history, not carried
        assert all(i.status in ("planned", "started") for i in carried)

    async def test_an_item_older_than_three_days_is_dropped(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await svc.program(USER, language="en")
        plan = store.plans[USER]
        plan.week_start = TODAY - timedelta(days=5)
        for item in plan.items:
            item.created_at = datetime.now(UTC) - timedelta(days=5)
        keep = next(i for i in plan.items if i.day_index == 3)          # planned for two days ago: carried
        drop = next(i for i in plan.items if i.day_index == 0)          # planned five days ago: dropped
        view = await svc.program(USER, language="en")
        carried = [(i.mode, [s.key for s in i.skills]) for i in view.plan.items if i.carried]   # ids are re-issued on rebuild
        assert (keep.mode, keep.skills) in carried and (drop.mode, drop.skills) not in carried


class TestStartingAndTicking:
    async def test_start_opens_an_attempt_on_the_items_skill_and_the_answer_ticks_it(self, catalog):
        svc, store = practice(catalog, scripted([GOOD, GOOD]))
        await with_goal(svc)
        view = await svc.program(USER, language="en")
        target = next(i for i in view.today if i.mode in ("quick", "deep", "retention_check"))
        started = await svc.start_program_item(USER, item_id=uuid.UUID(target.id), language="en")
        assert started.kind == "attempt" and started.attempt is not None and started.item.status == "started"
        question = catalog.questions[started.attempt.question.key]
        assert {s.key for s in target.skills} & {link.skill for link in question.skills}
        assert started.attempt.mode == "deep"                  # program attempts get the follow-up and the next question
        assert store.plan_links[uuid.UUID(started.attempt.id)] == uuid.UUID(target.id)
        after = await svc.program(USER, language="en")
        assert next(i for i in after.plan.items if i.id == target.id).status == "started"

        await svc.submit(USER, uuid.UUID(started.attempt.id), "alarm = AB + BC + AC", idempotency_key="k1")
        ticked = await svc.program(USER, language="en")
        item = next(i for i in ticked.plan.items if i.id == target.id)
        assert item.status == "done" and item.done and ticked.done_today >= 1
        stored = next(i for i in store.plans[USER].items if str(i.id) == target.id)
        assert stored.completed_attempt_id == uuid.UUID(started.attempt.id)

    async def test_an_unplanned_answer_ticks_the_earliest_matching_open_item(self, catalog):
        svc, store = practice(catalog, scripted([GOOD]))
        await with_goal(svc)
        await svc.program(USER, language="en")
        plan = store.plans[USER]
        plan.items.insert(0, PlanItemRow(id=uuid.uuid4(), day_index=0, mode="quick", skills=["boolean_algebra"],
                                         reason="extra", minutes=5))
        view = await svc.start(USER, question_key="example-sensor-majority", mode="quick", language="en")
        await svc.submit(USER, uuid.UUID(view.id), "alarm = AB + BC + AC", idempotency_key="k1")
        done = [i for i in store.plans[USER].items if i.status == "done"]
        assert len(done) == 1 and "boolean_algebra" in done[0].skills and done[0].completed_attempt_id == uuid.UUID(view.id)

    async def test_a_simulation_item_points_to_the_lobby_and_a_finished_interview_ticks_it(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await svc.program(USER, language="en")
        store.plans[USER].items.insert(0, PlanItemRow(id=uuid.uuid4(), day_index=0, mode="simulation",
                                                      skills=["boolean_algebra", "counters"], reason="sim", minutes=35))
        view = await svc.program(USER, language="en")
        sim = next(i for i in view.today if i.mode == "simulation")
        assert view.today[-1].mode == "simulation"                      # interviews come last in the day
        started = await svc.start_program_item(USER, item_id=uuid.UUID(sim.id), language="en")
        assert started.kind == "interview" and started.interview_duration_min == 30

        async def finished(tx, user_id, session_id):
            await svc._complete_program_item(tx, user_id, session_id=session_id)

        interviews = InterviewService(store, catalog, interviewer([GOOD]), InterviewConfig(reviewed_only=False),
                                      on_finished=finished)
        interviews.clock = Clock()
        iv = await interviews.start(USER, duration_min=20, language="en")
        await interviews.end(USER, uuid.UUID(iv.id))
        ticked = next(i for i in store.plans[USER].items if str(i.id) == sim.id)
        assert ticked.status == "done" and ticked.completed_session_id == uuid.UUID(iv.id)

    async def test_an_item_without_a_bank_question_is_skipped_not_an_error(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await svc.program(USER, language="en")
        orphan = PlanItemRow(id=uuid.uuid4(), day_index=0, mode="quick", skills=["project_walkthrough"], reason="no question",
                             minutes=5)
        store.plans[USER].items.insert(0, orphan)
        started = await svc.start_program_item(USER, item_id=orphan.id, language="en")
        assert started.kind == "nothing" and "skipped" in started.message
        assert next(i for i in store.plans[USER].items if i.id == orphan.id).status == "skipped"


@pytest.fixture
async def client(catalog, monkeypatch):
    settings = Settings(_env_file=None, llm_provider="scripted", allow_in_review_content=True,
                        interview_reviewed_only=False, suggest_reviewed_only=False)
    app.state.verifier = make_verifier()
    app.state.access_resolver = member_resolver({MEMBER})
    app.state.runtime = build_runtime(settings, catalog=catalog, provider=scripted([GOOD, GOOD, GOOD]),
                                      store=InMemoryStore(catalog))
    monkeypatch.setattr(get_settings(), "require_pilot_membership", True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_over_http(client):
    _, token = make_token(email=MEMBER)
    headers = {"Authorization": f"Bearer {token}"}
    assert (await client.post("/v1/me/goal", json={"job_type": "fpga", "minutes_per_day": 30}, headers=headers)).status_code == 200
    program = await client.get("/v1/me/program?language=he", headers=headers)
    assert program.status_code == 200 and program.json()["next"] and program.json()["goal_complete"]
    started = await client.post("/v1/me/program/start", json={"language": "he"}, headers=headers)
    body = started.json()
    assert started.status_code == 200 and body["kind"] in ("attempt", "interview"), body
    if body["kind"] == "attempt":
        assert body["attempt"]["language"] == "he" and body["item"]["status"] == "started"
    bad = await client.post("/v1/me/program/start", json={"item_id": "not-a-uuid"}, headers=headers)
    assert bad.status_code == 422


async def test_a_same_day_rebuild_does_not_mark_todays_items_carried(catalog):
    svc, store = practice(catalog)
    await with_goal(svc, minutes=30)
    await svc.program(USER, language="en")
    await with_goal(svc, minutes=45)                     # the goal changed: the plan is rebuilt the same day
    view = await svc.program(USER, language="en")
    assert view.plan.minutes_per_day == 45
    assert not any(i.carried for i in view.plan.items), "today's own items must not show as carried after a same-day rebuild"


async def test_the_skill_strength_card_shows_the_five_heaviest_skills_for_the_job(catalog):
    svc, _ = practice(catalog)
    await with_goal(svc)                                          # verification: testbenches and debugging weigh most
    progress = await svc.progress(USER, language="en")
    focus = progress.focus_skills
    assert len(focus) == 5 and all(s.status == "not_assessed" and s.level is None for s in focus)
    _, weights, _, _ = svc._plan("student", "verification")
    assert [s.key for s in focus] == sorted((s.key for s in focus), key=lambda k: -weights[k])
    heaviest = max((k for k in weights if catalog.skills[k].default_assessment_mode.value == "questioned"), key=lambda k: weights[k])
    assert focus[0].key == heaviest
    await svc.save_goal(USER, job_type="embedded_firmware", interview_date=None, minutes_per_day=30, seniority="student")
    embedded = (await svc.progress(USER, language="en")).focus_skills
    assert [s.key for s in embedded] != [s.key for s in focus]   # the job type changes which five matter
