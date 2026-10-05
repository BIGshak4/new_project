"""The saved program: built daily from the profile, carried forward, ticked by attempts and interviews, started
from the library. In-memory store, scripted model."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.engine import plan_router
from app.engine.catalog import load_catalog
from app.main import app
from app.repo.plans import OPEN, PlanItemRow
from app.runtime import build_runtime
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PROGRAM_MESSAGES, PracticeService, ServiceConfig
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


async def finish_day(svc, store, day_index=0, user=USER) -> int:
    """Mark every open item of one day (0 = today) done through the store, as finished answers would."""
    view = await svc.program(user, language="en")
    due = [i for i in view.plan.items if i.day_index == day_index and i.status in OPEN]
    async with store.transaction() as tx:
        for item in due:
            await tx.update_plan_item(uuid.UUID(item.id), status="done")
    return len(due)


def stored_item(store, item_id, user=USER) -> PlanItemRow:
    return next(i for i in store.plans[user].items if str(i.id) == str(item_id))


async def interview_once(svc, store, catalog):
    """A whole (short) mock interview, its end wired to the program the way the runtime wires it."""
    async def finished(tx, user_id, session_id):
        await svc._complete_program_item(tx, user_id, session_id=session_id)

    interviews = InterviewService(store, catalog, interviewer([GOOD]), InterviewConfig(reviewed_only=False),
                                  on_finished=finished)
    interviews.clock = Clock()
    iv = await interviews.start(USER, duration_min=20, language="en")
    await interviews.end(USER, uuid.UUID(iv.id))
    return iv


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

    async def test_carried_items_fill_todays_minutes_first_and_the_rest_wait_for_tomorrow(self, catalog):
        """Shaked, 2026-10-04: a skipped day no longer doubles today. Carried items count against today's minutes,
        the router fills only what is left, and carried items that do not fit move to the next day."""
        svc, store = practice(catalog)
        await with_goal(svc, minutes=30)
        await svc.program(USER, language="en")
        plan = store.plans[USER]
        old = datetime.now(UTC) - timedelta(days=1)
        plan.week_start = TODAY - timedelta(days=1)
        for item in plan.items:
            item.created_at = old
        for n, skill in enumerate(["counters", "truth_tables", "fsm_state_tables"]):            # a heavy day left undone
            plan.items.append(PlanItemRow(id=uuid.uuid4(), day_index=0, mode="deep", skills=[skill], reason=f"left {n}",
                                          minutes=20, status="planned", created_at=old))
        view = await svc.program(USER, language="en")
        today = [i for i in view.plan.items if i.day_index == 0]
        assert sum(i.minutes for i in today) <= 30, [(i.mode, i.minutes, i.carried) for i in today]
        waiting = [i for i in view.plan.items if i.day_index >= 1 and i.carried]
        assert waiting and all(i.status == "planned" for i in waiting)
        left = {i.reason for i in view.plan.items if i.reason.startswith("left ")}
        assert left == {"left 0", "left 1", "left 2"}                                           # nothing was lost
        for day in sorted({i.day_index for i in waiting}):
            assert sum(i.minutes for i in view.plan.items if i.day_index == day) <= 30 or \
                len([i for i in view.plan.items if i.day_index == day]) == 1

    async def test_an_opened_item_is_carried_into_today_even_when_today_is_full(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc, minutes=30)
        await svc.program(USER, language="en")
        plan = store.plans[USER]
        old = datetime.now(UTC) - timedelta(days=1)
        plan.week_start = TODAY - timedelta(days=1)
        for item in plan.items:
            item.created_at = old
        for n, skill in enumerate(["counters", "truth_tables"]):
            plan.items.append(PlanItemRow(id=uuid.uuid4(), day_index=0, mode="deep", skills=[skill], reason=f"left {n}",
                                          minutes=20, status="planned", created_at=old))
        opened = PlanItemRow(id=uuid.uuid4(), day_index=0, mode="deep", skills=["fsm_state_tables"], reason="opened",
                             minutes=20, status="started", created_at=old)
        plan.items.append(opened)
        view = await svc.program(USER, language="en")
        today = [i for i in view.plan.items if i.day_index == 0]
        assert any(i.reason == "opened" and i.status == "started" for i in today)

    async def test_a_carried_item_whose_skill_was_answered_since_is_dropped(self, catalog):
        svc, store = practice(catalog, scripted([GOOD, GOOD]))
        await with_goal(svc, minutes=30)
        view = await svc.start(USER, question_key="example-sensor-majority", mode="quick", language="en")
        await svc.submit(USER, uuid.UUID(view.id), "alarm = AB + BC + AC", idempotency_key="k1")     # boolean_algebra has a profile row
        await svc.program(USER, language="en")
        plan = store.plans[USER]
        old = datetime.now(UTC) - timedelta(days=1)
        plan.week_start = TODAY - timedelta(days=1)
        for item in plan.items:
            item.created_at = old
        plan.items.append(PlanItemRow(id=uuid.uuid4(), day_index=0, mode="deep", skills=["boolean_algebra"], reason="stale plan",
                                      minutes=20, status="planned", created_at=old))
        plan.items.append(PlanItemRow(id=uuid.uuid4(), day_index=0, mode="quick", skills=["counters"], reason="still open",
                                      minutes=4, status="planned", created_at=old))
        for (uid, key), row in store.profiles.items():                       # an interview scored boolean_algebra since
            if uid == USER and key == "boolean_algebra":
                row["last_assessed_at"] = datetime.now(UTC)
        view = await svc.program(USER, language="en")
        reasons = {i.reason for i in view.plan.items if i.carried}
        assert "still open" in reasons and "stale plan" not in reasons

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


class TestWorkingAhead:
    """'I want to be able to start tomorrow's plan after I finished today's plan' (Shaked, 2026-10-03)."""

    async def test_a_later_days_item_waits_while_today_has_open_items(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        view = await svc.program(USER, language="en")
        assert view.today and view.ahead is None
        tomorrow = next(i for i in view.plan.items if i.day_index == 1)
        for language in ("he", "en"):
            refused = await svc.start_program_item(USER, item_id=uuid.UUID(tomorrow.id), language=language)
            assert refused.kind == "nothing" and refused.attempt is None and refused.item.id == tomorrow.id
            assert refused.message == PROGRAM_MESSAGES[language]["finish_today_first"]
        assert "קודם מסיימים" in PROGRAM_MESSAGES["he"]["finish_today_first"]
        assert not store.attempts and not store.plan_links                  # nothing was created
        assert stored_item(store, tomorrow.id).status == "planned"

    async def test_once_today_is_done_tomorrows_first_item_opens_and_its_answer_ticks_it(self, catalog):
        svc, store = practice(catalog, scripted([GOOD, GOOD]))
        await with_goal(svc)
        due_today = await finish_day(svc, store)
        view = await svc.program(USER, language="en")
        tomorrow = [i for i in view.plan.items if i.day_index == 1]
        assert view.today == [] and view.next is None and view.done_today == due_today
        assert view.ahead is not None and view.ahead.id == tomorrow[0].id and view.ahead.day_index == 1

        started = await svc.start_program_item(USER, item_id=uuid.UUID(view.ahead.id), language="en")
        assert started.kind == "attempt" and started.attempt.mode == "deep" and started.item.status == "started"
        assert store.plan_links[uuid.UUID(started.attempt.id)] == uuid.UUID(view.ahead.id)
        question = catalog.questions[started.attempt.question.key]
        assert {s.key for s in view.ahead.skills} & {link.skill for link in question.skills}

        await svc.submit(USER, uuid.UUID(started.attempt.id), "alarm = AB + BC + AC", idempotency_key="k1")
        after = await svc.program(USER, language="en")
        ticked = next(i for i in after.plan.items if i.id == view.ahead.id)
        assert ticked.status == "done" and ticked.day_index == 1
        assert stored_item(store, view.ahead.id).completed_attempt_id == uuid.UUID(started.attempt.id)
        assert after.done_today == view.done_today                          # tomorrow's work is not today's count
        assert after.ahead is not None and after.ahead.id == tomorrow[1].id

    async def test_after_tomorrow_is_done_too_the_day_after_opens(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await finish_day(svc, store, 0)
        await finish_day(svc, store, 1)
        view = await svc.program(USER, language="en")
        day_after = [i for i in view.plan.items if i.day_index == 2 and i.status in OPEN]
        assert view.today == [] and day_after
        assert view.ahead is not None and view.ahead.id == day_after[0].id and view.ahead.day_index == 2
        started = await svc.start_program_item(USER, item_id=uuid.UUID(view.ahead.id), language="en")
        assert started.kind == "attempt" and started.item.id == view.ahead.id

    async def test_start_without_an_item_opens_the_ahead_item_once_today_is_done(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await finish_day(svc, store)
        view = await svc.program(USER, language="en")
        started = await svc.start_program_item(USER, language="en")
        assert started.kind == "attempt" and started.item.id == view.ahead.id
        assert store.plan_links[uuid.UUID(started.attempt.id)] == uuid.UUID(view.ahead.id)
        # an unknown item falls back the same way: today's next, else the ahead item
        fallback = await svc.start_program_item(USER, item_id=uuid.uuid4(), language="en")
        assert fallback.kind == "attempt" and fallback.item.id == view.ahead.id

    async def test_an_unplanned_answer_never_ticks_a_later_day_even_when_today_is_done(self, catalog):
        svc, store = practice(catalog, scripted([GOOD]))
        await with_goal(svc)
        await finish_day(svc, store)
        tomorrow = PlanItemRow(id=uuid.uuid4(), day_index=1, mode="quick", skills=["boolean_algebra"], reason="tomorrow",
                               minutes=5)
        store.plans[USER].items.insert(0, tomorrow)
        before = {i.id: i.status for i in store.plans[USER].items}
        view = await svc.start(USER, question_key="example-sensor-majority", mode="quick", language="en")
        await svc.submit(USER, uuid.UUID(view.id), "alarm = AB + BC + AC", idempotency_key="k1")
        assert {i.id: i.status for i in store.plans[USER].items} == before        # nothing ticked
        assert stored_item(store, tomorrow.id).status == "planned"

    async def test_a_later_simulation_item_opens_the_lobby_and_the_finished_interview_ticks_it(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await svc.program(USER, language="en")
        # stamped like the plan's own items and listed first, so tomorrow's view order puts it first: only the
        # "interviews last" rule keeps it from being the item ahead (no dependence on the clock)
        sim = PlanItemRow(id=uuid.uuid4(), day_index=1, mode="simulation", skills=["boolean_algebra", "counters"],
                          reason="sim", minutes=35, created_at=store.plans[USER].generated_at)
        store.plans[USER].items.insert(0, sim)
        assert [i.id for i in (await svc.program(USER, language="en")).plan.items if i.day_index == 1][0] == str(sim.id)
        refused = await svc.start_program_item(USER, item_id=sim.id, language="en")
        assert refused.kind == "nothing" and stored_item(store, sim.id).status == "planned"

        await finish_day(svc, store)
        view = await svc.program(USER, language="en")
        assert view.ahead.day_index == 1 and view.ahead.mode != "simulation"   # interviews come last in the day
        started = await svc.start_program_item(USER, item_id=sim.id, language="en")
        assert started.kind == "interview" and started.interview_duration_min == 30 and started.item.status == "started"
        assert stored_item(store, sim.id).status == "started"

        iv = await interview_once(svc, store, catalog)
        ticked = stored_item(store, sim.id)
        assert ticked.status == "done" and ticked.completed_session_id == uuid.UUID(iv.id)

    async def test_the_item_ahead_is_the_earliest_day_even_when_that_day_is_only_an_interview(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await svc.program(USER, language="en")
        plan = store.plans[USER]
        sim = PlanItemRow(id=uuid.uuid4(), day_index=1, mode="simulation", skills=["boolean_algebra", "counters"],
                          reason="sim", minutes=35, created_at=plan.generated_at)
        plan.items = [sim, *(i for i in plan.items if i.day_index != 1)]          # tomorrow holds only an interview
        await finish_day(svc, store)
        view = await svc.program(USER, language="en")
        assert [i.day_index for i in view.plan.items if i.status in OPEN and i.day_index > 1]     # the day after has work
        assert view.ahead is not None and view.ahead.id == str(sim.id) and view.ahead.day_index == 1

    async def test_with_two_later_interviews_opened_the_earliest_day_is_ticked(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await finish_day(svc, store)
        later, sooner = (PlanItemRow(id=uuid.uuid4(), day_index=day, mode="simulation", skills=["boolean_algebra", "counters"],
                                     reason=f"sim on day {day}", minutes=35) for day in (3, 2))
        store.plans[USER].items[:0] = [later, sooner]                           # the later day listed first
        for sim in (later, sooner):
            started = await svc.start_program_item(USER, item_id=sim.id, language="en")
            assert started.kind == "interview" and stored_item(store, sim.id).status == "started"
        iv = await interview_once(svc, store, catalog)
        assert stored_item(store, sooner.id).status == "done"
        assert stored_item(store, sooner.id).completed_session_id == uuid.UUID(iv.id)
        assert stored_item(store, later.id).status == "started"

    async def test_an_interview_not_opened_from_the_program_leaves_a_later_simulation_alone(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await finish_day(svc, store)
        sim = PlanItemRow(id=uuid.uuid4(), day_index=1, mode="simulation", skills=["boolean_algebra", "counters"],
                          reason="sim", minutes=35)
        store.plans[USER].items.insert(0, sim)
        before = {i.id: i.status for i in store.plans[USER].items}
        await interview_once(svc, store, catalog)                               # from the interview page, not the plan
        assert {i.id: i.status for i in store.plans[USER].items} == before        # nothing ticked
        assert stored_item(store, sim.id).status == "planned" and stored_item(store, sim.id).completed_session_id is None

    async def test_a_done_or_skipped_later_days_item_is_never_reopened(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc, minutes=60)                       # three or more items a day
        view = await svc.program(USER, language="en")
        tomorrow = [i for i in view.plan.items if i.day_index == 1]
        assert len(tomorrow) >= 3
        done_id, skipped_id = uuid.UUID(tomorrow[0].id), uuid.UUID(tomorrow[1].id)
        async with store.transaction() as tx:
            await tx.update_plan_item(done_id, status="done")
            await tx.update_plan_item(skipped_id, status="skipped")
        # while today is open, a finished item of tomorrow falls back to today's next item (not "finish today first")
        started = await svc.start_program_item(USER, item_id=done_id, language="en")
        assert started.kind == "attempt" and started.item.id == view.next.id and started.item.day_index == 0
        # once today is done, it falls back to the item ahead
        await finish_day(svc, store)
        view = await svc.program(USER, language="en")
        assert view.ahead is not None and view.ahead.id == tomorrow[2].id
        for finished in (done_id, skipped_id):
            again = await svc.start_program_item(USER, item_id=finished, language="en")
            assert again.kind == "attempt" and again.item.id == view.ahead.id
        assert stored_item(store, done_id).status == "done" and stored_item(store, skipped_id).status == "skipped"
        assert done_id not in store.plan_links.values() and skipped_id not in store.plan_links.values()

    async def test_the_next_days_rebuild_keeps_work_done_ahead(self, catalog, monkeypatch):
        svc, store = practice(catalog, scripted([GOOD, GOOD]))
        await with_goal(svc)
        await finish_day(svc, store)
        ahead = (await svc.program(USER, language="en")).ahead
        started = await svc.start_program_item(USER, item_id=uuid.UUID(ahead.id), language="en")
        await svc.submit(USER, uuid.UUID(started.attempt.id), "alarm = AB + BC + AC", idempotency_key="k1")
        signature = (ahead.mode, [s.key for s in ahead.skills])

        # the router plans the same activity for the new today (and, to show only that day is affected, on day 3)
        real_router = svc._router_items

        def router(*args, **kwargs):
            routed = [p for p in real_router(*args, **kwargs) if (p.activity.mode, p.activity.skills) != signature]
            same = [plan_router.PlannedItem(day, plan_router.Activity(signature[0], list(signature[1]), ahead.minutes,
                                                                      reason_code="unassessed")) for day in (0, 3)]
            return sorted([*same, *routed], key=lambda p: p.day_index)

        monkeypatch.setattr(svc, "_router_items", router)
        plan = store.plans[USER]                                    # imitate: this plan was built yesterday, so
        plan.week_start = TODAY - timedelta(days=1)                 # the item done ahead is planned for today
        for item in plan.items:
            item.created_at = datetime.now(UTC) - timedelta(days=1)

        rebuilt = await svc.program(USER, language="en")
        assert rebuilt.plan.generated_for == TODAY.isoformat()
        on_day = [i for i in rebuilt.plan.items if (i.mode, [s.key for s in i.skills]) == signature]
        kept = [i for i in on_day if i.day_index == 0]
        assert len(kept) == 1 and kept[0].status == "done" and kept[0].done and not kept[0].carried
        assert stored_item(store, kept[0].id).completed_attempt_id == uuid.UUID(started.attempt.id)
        assert kept[0].id not in [i.id for i in rebuilt.today]
        assert rebuilt.done_today == 1                              # yesterday's done items are history
        assert [i.status for i in on_day if i.day_index == 3] == ["planned"]   # other days keep the router's item

    async def test_a_day_finished_ahead_is_not_refilled_the_next_morning(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc, minutes=30)
        for day in (0, 1, 2):                                       # today, then two days ahead
            await finish_day(svc, store, day)
        plan = store.plans[USER]
        done_minutes = {day: sum(i.minutes for i in plan.items if i.day_index == day) for day in (1, 2)}
        assert all(done_minutes.values())
        plan.week_start = TODAY - timedelta(days=1)                 # the next morning
        for item in plan.items:
            item.created_at = datetime.now(UTC) - timedelta(days=1)

        rebuilt = await svc.program(USER, language="en")
        assert rebuilt.plan.generated_for == TODAY.isoformat()
        for new_day, old_day in ((0, 1), (1, 2)):
            on_day = [i for i in rebuilt.plan.items if i.day_index == new_day]
            done = sum(i.minutes for i in on_day if i.done)
            due = sum(i.minutes for i in on_day if not i.done)
            assert done == done_minutes[old_day] and not any(i.carried for i in on_day)
            # the work done ahead is the day's work: the router fills only the minutes it left
            assert done + due <= max(30, done), (new_day, [(i.mode, i.minutes, i.status) for i in on_day])
        if done_minutes[1] > 30 - 4:                                # no room left for even a quick item
            assert rebuilt.today == [] and rebuilt.ahead is not None and rebuilt.ahead.day_index >= 1
        assert rebuilt.done_today == len([i for i in plan.items if i.day_index == 1])

    async def test_an_item_done_ahead_for_today_is_not_also_carried_open(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await svc.program(USER, language="en")
        plan = store.plans[USER]
        plan.week_start = TODAY - timedelta(days=1)                 # imitate: this plan was built yesterday
        old = datetime.now(UTC) - timedelta(days=1)
        for item in plan.items:
            item.created_at = old
        plan.items += [PlanItemRow(id=uuid.uuid4(), day_index=0, mode="quick", skills=["counters"], reason="left open",
                                   minutes=4, created_at=old),
                       PlanItemRow(id=uuid.uuid4(), day_index=1, mode="quick", skills=["counters"], reason="done ahead",
                                   minutes=4, status="done", created_at=old)]
        rebuilt = await svc.program(USER, language="en")
        today = [i for i in rebuilt.plan.items if i.day_index == 0 and (i.mode, [s.key for s in i.skills]) == ("quick", ["counters"])]
        assert [(i.status, i.reason) for i in today] == [("done", "done ahead")]

    async def test_the_next_days_rebuild_keeps_an_interview_done_ahead(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await svc.program(USER, language="en")
        sim = PlanItemRow(id=uuid.uuid4(), day_index=1, mode="simulation", skills=["boolean_algebra", "counters"],
                          reason="sim", minutes=35)
        store.plans[USER].items.insert(0, sim)
        await finish_day(svc, store)
        assert (await svc.start_program_item(USER, item_id=sim.id, language="en")).kind == "interview"
        iv = await interview_once(svc, store, catalog)
        plan = store.plans[USER]
        plan.week_start = TODAY - timedelta(days=1)                 # the next morning
        for item in plan.items:
            item.created_at = datetime.now(UTC) - timedelta(days=1)

        rebuilt = await svc.program(USER, language="en")
        kept = [i for i in store.plans[USER].items if i.completed_session_id == uuid.UUID(iv.id)]
        assert len(kept) == 1 and kept[0].id != sim.id                # the rebuild issues new ids
        assert (kept[0].day_index, kept[0].mode, kept[0].status) == (0, "simulation", "done")
        shown = next(i for i in rebuilt.plan.items if i.id == str(kept[0].id))
        assert shown.done and not shown.carried and rebuilt.done_today == 1

    async def test_an_item_opened_ahead_and_answered_after_the_next_mornings_rebuild_ticks_that_item(self, catalog):
        svc, store = practice(catalog, scripted([GOOD, GOOD]))
        await with_goal(svc)
        await finish_day(svc, store, 0)
        await finish_day(svc, store, 1)
        view = await svc.program(USER, language="en")
        assert view.ahead is not None and view.ahead.day_index == 2
        started = await svc.start_program_item(USER, item_id=uuid.UUID(view.ahead.id), language="en")
        attempt = uuid.UUID(started.attempt.id)
        signature = (view.ahead.mode, tuple(s.key for s in view.ahead.skills))

        plan = store.plans[USER]
        plan.week_start = TODAY - timedelta(days=1)                 # the next morning, before answering
        for item in plan.items:
            item.created_at = datetime.now(UTC) - timedelta(days=1)
        rebuilt = await svc.program(USER, language="en")
        kept = [i for i in rebuilt.plan.items if (i.mode, tuple(s.key for s in i.skills)) == signature and i.day_index == 1]
        assert len(kept) == 1, [(i.day_index, i.mode, i.status) for i in rebuilt.plan.items]
        copy = kept[0]
        assert copy.status == "started" and not copy.carried and copy.id != view.ahead.id
        assert store.plan_links[attempt] == uuid.UUID(copy.id)      # the open attempt follows its item
        open_today_before = {i.id for i in rebuilt.today}

        await svc.submit(USER, attempt, "alarm = AB + BC + AC", idempotency_key="k-ahead")
        after = await svc.program(USER, language="en")
        assert next(i for i in after.plan.items if i.id == copy.id).status == "done"
        assert {i.id for i in after.today} == open_today_before      # no item of today was ticked instead

    async def test_an_item_opened_ahead_that_rolls_into_today_stays_started_and_its_answer_ticks_it(self, catalog):
        svc, store = practice(catalog, scripted([GOOD, GOOD]))
        await with_goal(svc)
        await finish_day(svc, store, 0)
        view = await svc.program(USER, language="en")
        assert view.ahead is not None and view.ahead.day_index == 1
        started = await svc.start_program_item(USER, item_id=uuid.UUID(view.ahead.id), language="en")
        attempt = uuid.UUID(started.attempt.id)
        signature = (view.ahead.mode, tuple(s.key for s in view.ahead.skills))

        plan = store.plans[USER]
        plan.week_start = TODAY - timedelta(days=1)                 # the next morning: that item is now due today
        for item in plan.items:
            item.created_at = datetime.now(UTC) - timedelta(days=1)
        rebuilt = await svc.program(USER, language="en")
        copy = next(i for i in rebuilt.today if (i.mode, tuple(s.key for s in i.skills)) == signature)
        assert copy.status == "started" and store.plan_links[attempt] == uuid.UUID(copy.id)

        await svc.submit(USER, attempt, "alarm = AB + BC + AC", idempotency_key="k-roll")
        after = await svc.program(USER, language="en")
        assert next(i for i in after.plan.items if i.id == copy.id).status == "done"
        assert sum(1 for i in after.plan.items if i.day_index == 0 and i.status == "done") == 1

    async def test_a_rest_day_lets_the_following_days_start(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await svc.program(USER, language="en")
        store.plans[USER].items = [i for i in store.plans[USER].items if i.day_index != 0]     # nothing due today
        view = await svc.program(USER, language="en")
        assert view.today == [] and view.next is None and view.done_today == 0
        assert view.ahead is not None and view.ahead.day_index == 1
        later = next(i for i in view.plan.items if i.day_index == 2)
        started = await svc.start_program_item(USER, item_id=uuid.UUID(later.id), language="en")
        assert started.kind == "attempt" and started.item.id == later.id


class TestReadinessForTheJobType:
    """Shaked, 2026-10-05: the user chooses a job type; this view says where they stand against its demands."""

    async def test_without_a_goal_it_asks_for_one(self, catalog):
        svc, _ = practice(catalog)
        view = await svc.readiness(USER, language="en")
        assert view.job_type is None and view.skills == [] and "Choose the job type" in view.message

    async def test_a_new_user_sees_the_demands_heaviest_first_and_what_to_answer(self, catalog):
        svc, _ = practice(catalog)
        await with_goal(svc)
        view = await svc.readiness(USER, language="en")
        assert view.job_type == "verification" and view.job_type_label and not view.ready_to_judge
        assert view.readiness_word is None and view.readiness_score is None and view.coverage == 0.0
        shares = [s.weight_share for s in view.skills]
        assert shares == sorted(shares, reverse=True) and abs(sum(shares) - 1) < 0.02
        assert all(s.status == "not_assessed" and s.gap is None and s.freshness == "none" for s in view.skills)
        assert any(not s.askable for s in view.skills)                                  # the blind skills are named
        assert 1 <= len(view.next_questions) <= 3 and len({q.skill for q in view.next_questions}) == len(view.next_questions)
        askable_heaviest = [s.key for s in view.skills if s.askable][:6]
        assert all(q.skill in askable_heaviest and q.why == "unassessed" for q in view.next_questions)
        assert "Not enough evidence yet" in view.message

    async def test_an_answer_shows_up_with_its_level_and_freshness_and_expiry_drops_it(self, catalog):
        svc, store = practice(catalog, scripted([GOOD, GOOD]))
        await with_goal(svc)
        view = await svc.start(USER, question_key="example-sensor-majority", mode="quick", language="en")
        await svc.submit(USER, uuid.UUID(view.id), "alarm = AB + BC + AC", idempotency_key="k1")
        ready = await svc.readiness(USER, language="en")
        boolean = next(s for s in ready.skills if s.key == "boolean_algebra")
        assert boolean.level is not None and boolean.freshness == "fresh"
        assert boolean.status in ("assessed", "insufficient_evidence")
        if boolean.status == "assessed":
            assert boolean.gap is not None and ready.coverage > 0
        # seven weeks later the evidence has expired: the level is shown as history, the skill counts as unknown again
        for (uid, _key), row in store.profiles.items():
            if uid == USER and row.get("last_assessed_at"):
                row["last_assessed_at"] = row["last_assessed_at"] - timedelta(days=50)
        store.plans.clear()
        later = await svc.readiness(USER, language="en")
        boolean = next(s for s in later.skills if s.key == "boolean_algebra")
        assert boolean.freshness == "expired" and boolean.gap is None and boolean.level is not None
        assert later.coverage == 0.0 and any(q.skill == "boolean_algebra" and q.why == "refresh" for q in later.next_questions)

    async def test_the_word_appears_only_with_enough_evidence(self, catalog, monkeypatch):
        svc, _ = practice(catalog, scripted([GOOD, GOOD, GOOD]))
        await with_goal(svc)
        view = await svc.start(USER, question_key="example-sensor-majority", mode="deep", language="en")
        aid = uuid.UUID(view.id)
        _, view = await svc.submit(USER, aid, "alarm = AB + BC + AC", idempotency_key="k1")
        while view.pending_follow_up is not None:                                       # two scored answers: assessed
            _, view = await svc.submit(USER, aid, "pairs", idempotency_key=f"f{view.pending_follow_up.turn}",
                                       follow_up_turn=view.pending_follow_up.turn)
        before = await svc.readiness(USER, language="en")
        assert before.coverage > 0 and not before.ready_to_judge and before.readiness_word is None
        monkeypatch.setattr(PracticeService, "READY_COVERAGE", 0.0)                   # the gate alone decides
        after = await svc.readiness(USER, language="en")
        assert after.ready_to_judge and after.readiness_word in ("Ready", "Nearly there", "On the way", "Early days")
        assert after.readiness_score is not None and after.job_type_label in after.message
        hebrew = await svc.readiness(USER, language="he")
        assert hebrew.readiness_word in ("מוכנים", "כמעט שם", "בדרך", "בתחילת הדרך")

    async def test_the_view_writes_nothing(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await svc.program(USER, language="en")
        snapshot = (len(store.metrics), len(store.usage), str(sorted(store.plans[USER].items, key=lambda i: str(i.id))))
        await svc.readiness(USER, language="en")
        assert (len(store.metrics), len(store.usage), str(sorted(store.plans[USER].items, key=lambda i: str(i.id)))) == snapshot


class TestChangingTheJobType:
    async def test_a_new_job_type_rebuilds_the_plan_at_once_and_keeps_what_was_done(self, catalog):
        """Shaked, 2026-10-05: not the next morning."""
        svc, store = practice(catalog)
        await with_goal(svc)
        first = await svc.program(USER, language="en")
        generated = store.plans[USER].generated_at
        done = await finish_day(svc, store)                                             # today's work, done
        assert done >= 1
        await svc.program(USER, language="en")
        assert store.plans[USER].generated_at == generated                              # a plain read reuses the plan
        await svc.save_goal(USER, job_type="software", interview_date=TODAY + timedelta(days=10), minutes_per_day=30,
                            seniority="student")
        second = await svc.program(USER, language="en")
        assert store.plans[USER].generated_at > generated                               # rebuilt now
        assert second.plan.generated_for == first.plan.generated_for == TODAY.isoformat()
        assert second.done_today == done                                                # nothing done was lost
        assert not any(i.carried for i in second.plan.items)                            # a same-day rebuild carries nothing
        rebuilt_at = store.plans[USER].generated_at
        again = await svc.program(USER, language="en")
        assert store.plans[USER].generated_at == rebuilt_at and again.done_today == done

    async def test_saving_the_same_goal_twice_does_not_churn_the_plan_twice(self, catalog):
        svc, store = practice(catalog)
        await with_goal(svc)
        await svc.program(USER, language="en")
        await with_goal(svc)                                                           # saved again, unchanged
        await svc.program(USER, language="en")
        rebuilt_at = store.plans[USER].generated_at
        await svc.program(USER, language="en")
        assert store.plans[USER].generated_at == rebuilt_at                            # reused once rebuilt


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


async def test_over_http_the_program_names_the_item_ahead_once_today_is_done(client):
    user, token = make_token(email=MEMBER)
    headers = {"Authorization": f"Bearer {token}"}
    assert (await client.post("/v1/me/goal", json={"job_type": "fpga", "minutes_per_day": 30}, headers=headers)).status_code == 200
    program = (await client.get("/v1/me/program?language=en", headers=headers)).json()
    assert "ahead" in program and program["ahead"] is None and program["today"]
    runtime = app.state.runtime
    await finish_day(runtime.practice, runtime.store, user=user)
    program = (await client.get("/v1/me/program?language=en", headers=headers)).json()
    assert program["today"] == [] and program["next"] is None
    assert program["ahead"] is not None and program["ahead"]["day_index"] >= 1 and program["ahead"]["id"]
    started = (await client.post("/v1/me/program/start", json={"item_id": program["ahead"]["id"]}, headers=headers)).json()
    assert started["kind"] in ("attempt", "interview") and started["item"]["id"] == program["ahead"]["id"], started


async def test_a_same_day_rebuild_does_not_mark_todays_items_carried(catalog):
    svc, store = practice(catalog)
    await with_goal(svc, minutes=30)
    await svc.program(USER, language="en")
    await with_goal(svc, minutes=45)                     # the goal changed: the plan is rebuilt the same day
    view = await svc.program(USER, language="en")
    assert view.plan.minutes_per_day == 45
    assert not any(i.carried for i in view.plan.items), "today's own items must not show as carried after a same-day rebuild"


async def test_the_skill_strength_card_never_shows_a_skill_no_question_examines(catalog):
    svc, _ = practice(catalog)
    await with_goal(svc)
    progress = await svc.progress(USER, language="en")
    askable = {link.skill for q in catalog.questions.values() for link in q.skills}
    assert progress.focus_skills and all(s.key in askable for s in progress.focus_skills)
    assert "latches_flip_flops" not in [s.key for s in progress.focus_skills]        # no live question yet


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
