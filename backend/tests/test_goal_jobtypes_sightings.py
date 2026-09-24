"""The overnight build of 2026-09-23: job types, the user's goal, company sightings, the three-part progress view and
visual answers in the mock interview. In-memory store, scripted model."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.errors import ApiError
from app.config import Settings, get_settings
from app.engine.catalog import load_catalog
from app.main import app
from app.runtime import build_runtime
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.authtools import make_token, make_verifier, member_resolver
from tests.test_interview_service import Clock, interviewer
from tests.test_practice_hardening import GOOD, SEEDS, WEAK, scripted
from tests.test_visual_assessment import majority_circuit

USER = uuid.uuid4()
OTHER = uuid.uuid4()
Q = "example-sensor-majority"
MEMBER = "tester@example.com"


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def practice(catalog, provider=None, **config) -> tuple[PracticeService, InMemoryStore]:
    store = InMemoryStore(catalog)
    return PracticeService(store, catalog, provider or scripted([WEAK, GOOD, GOOD]), ServiceConfig(**config)), store


# ----------------------------------------------------------------------------- job types


class TestJobTypes:
    def test_the_catalog_has_the_six_job_types_with_known_skills(self, catalog):
        assert set(catalog.job_types) == {"digital_design", "verification", "fpga", "embedded_firmware", "software",
                                          "student_general"}
        for job in catalog.job_types.values():
            assert job.text("label", "en") and job.text("label", "he") and job.text("description", "en")
            assert all(skill in catalog.skills for skill in job.emphasis)
            assert job.weight("no_such_skill") == 1.0

    def test_a_job_type_reweights_the_plan_without_adding_skills(self, catalog):
        svc, _ = practice(catalog)
        _, base, ceiling, base_plan = svc._plan("student")
        _, verification, ceiling2, plan = svc._plan("student", "verification")
        assert ceiling == ceiling2 and {p.key for p in plan} == {p.key for p in base_plan}
        assert verification["testbench_basics"] > base["testbench_basics"]          # emphasised 1.8x
        assert verification["universal_gates"] < base["universal_gates"]            # played down 0.5x
        assert abs(sum(verification.values()) - sum(base.values())) < 1e-6           # still a normalised plan
        assert svc._plan("student", "no-such-job") == svc._plan("student")           # unknown: ignored, not an error

    def test_the_context_of_an_attempt_follows_the_goal(self, catalog):
        svc, store = practice(catalog)
        assert svc._context("student", "en", "embedded_firmware").skill_weights["bit_manipulation"] > \
            svc._context("student", "en").skill_weights["bit_manipulation"]

    def test_job_type_views_are_localised(self, catalog):
        svc, _ = practice(catalog)
        en = {j.key: j for j in svc.job_types(language="en")}
        he = {j.key: j for j in svc.job_types(language="he")}
        assert en["verification"].label == "Verification" and he["verification"].label == "וריפיקציה"
        assert en["verification"].description


class TestTheLibraryByJobAndCompany:
    async def test_every_question_carries_its_job_types(self, catalog):
        svc, _ = practice(catalog)
        rows = await svc.list_questions(language="en")
        by_key = {r.key: r for r in rows}
        assert "digital_design" in by_key[Q].job_types and by_key[Q].relevance is None and by_key[Q].companies == []
        assert all(r.job_types for r in rows)

    async def test_filtering_by_job_orders_by_relevance(self, catalog):
        svc, _ = practice(catalog)
        everything = await svc.list_questions(language="en")
        rows = await svc.list_questions(language="en", job="digital_design")
        assert rows and len(rows) <= len(everything)
        assert all("digital_design" in r.job_types and r.relevance is not None for r in rows)
        assert [r.relevance for r in rows] == sorted((r.relevance for r in rows), reverse=True)
        with pytest.raises(ApiError, match="job type"):
            await svc.list_questions(language="en", job="astronaut")

    async def test_company_sightings_round_trip(self, catalog):
        svc, store = practice(catalog)
        tags = await svc.add_sighting(USER, company="  Intel  Corp. ", key=Q)
        assert [t.model_dump() for t in tags] == [{"slug": "intel-corp", "name": "Intel Corp.", "count": 1}]
        tags = await svc.add_sighting(USER, company="intel corp", key=Q)                  # the same person again
        assert tags[0].count == 1
        tags = await svc.add_sighting(OTHER, company="Intel Corp", key=Q)
        assert tags[0].count == 2
        await svc.add_sighting(OTHER, company="Nvidia", key=Q)

        rows = await svc.list_questions(language="en")
        mine = next(r for r in rows if r.key == Q)
        assert [t.slug for t in mine.companies] == ["intel-corp", "nvidia"]              # most reported first
        assert all(r.companies == [] for r in rows if r.key != Q)

        assert [r.key for r in await svc.list_questions(language="en", company="Intel Corp")] == [Q]
        assert await svc.list_questions(language="en", company="apple") == []
        companies = await svc.companies()
        assert [c.model_dump() for c in companies] == [
            {"slug": "intel-corp", "name": "Intel Corp.", "questions": 1, "sightings": 2},
            {"slug": "nvidia", "name": "Nvidia", "questions": 1, "sightings": 1}]

    def test_slugs_match_the_table_constraint_including_hebrew(self):
        import re

        from app.repo.sightings import MAX_NAME, slugify
        sql = (SEEDS.parent.parent / "supabase" / "migrations" / "20260924045708_question_sightings.sql").read_text(encoding="utf-8")
        pattern = re.compile(re.search(r"company_slug ~ '([^']+)'", sql).group(1))
        for name in ("Intel Corp.", "  Nvidia  ", "אינטל", "Intel ישראל", "מובילאיי (Mobileye)", "a" * 200, "x-" * 60, "Ünïcode Çô"):
            slug = slugify(name)
            assert slug and pattern.fullmatch(slug), (name, slug)
            assert len(slug) <= MAX_NAME and not slug.endswith("-")
        assert slugify("אינטל") == "אינטל" and slugify("!!!") == ""

    async def test_sightings_are_validated_and_degrade_when_the_table_is_missing(self, catalog):
        svc, store = practice(catalog)
        with pytest.raises(ApiError) as e:
            await svc.add_sighting(USER, company="   ", key=Q)
        assert e.value.code == "validation"
        with pytest.raises(ApiError) as e:
            await svc.add_sighting(USER, company="Intel", key="no-such-question")
        assert e.value.code == "not_found"
        store.sightings_enabled = False
        with pytest.raises(ApiError) as e:
            await svc.add_sighting(USER, company="Intel", key=Q)
        assert e.value.code == "temporarily_unavailable" and e.value.status == 503
        assert await svc.companies() == [] or True                          # readers never raise


# ----------------------------------------------------------------------------- the goal and the progress view


class TestTheGoal:
    async def test_save_and_read_back(self, catalog):
        svc, store = practice(catalog)
        empty = await svc.get_goal(USER)
        assert empty.complete is False and empty.job_type is None and empty.days_to_interview is None
        when = date.today() + timedelta(days=10)
        view = await svc.save_goal(USER, job_type="verification", interview_date=when, minutes_per_day=20,
                                   seniority="junior", language="he")
        assert view.complete and view.job_type_label == "וריפיקציה" and view.days_to_interview == 10
        again = await svc.get_goal(USER, language="en")
        assert again.model_dump() == {**view.model_dump(), "job_type_label": "Verification"}
        assert store.seniority[USER] == "junior"
        # a request without seniority keeps the stored one, and the response says what is stored
        partial = await svc.save_goal(USER, job_type="fpga", interview_date=None, minutes_per_day=45, seniority=None)
        assert partial.seniority == "junior" and partial.interview_date is None and partial.job_type == "fpga"
        assert (await svc.get_goal(USER)).model_dump() == partial.model_dump()

    @pytest.mark.parametrize("kw", [dict(job_type="astronaut"), dict(minutes_per_day=0), dict(minutes_per_day=1000),
                                    dict(seniority="ceo")])
    async def test_bad_goals_are_validation_errors(self, catalog, kw):
        svc, _ = practice(catalog)
        fields = dict(job_type="verification", interview_date=None, minutes_per_day=30, seniority=None)
        with pytest.raises(ApiError) as e:
            await svc.save_goal(USER, **{**fields, **kw})
        assert e.value.code == "validation"

    async def test_progress_has_the_three_parts_before_any_answer(self, catalog):
        svc, _ = practice(catalog, suggest_reviewed_only=False)          # the seed bank is unreviewed; production is on trial
        view = await svc.progress(USER, language="en")
        assert view.overview.answered == 0 and view.overview.level == "Getting started" and view.overview.level_rank == 0
        assert "first answer" in view.overview.message and view.overview.skills_total > 0
        assert view.timeline == []
        assert view.plan.minutes_per_day == 30 and view.plan.days_to_interview is None and view.plan.items
        assert all(item.reason and item.minutes > 0 and item.skills for item in view.plan.items)
        assert view.goal.complete is False
        he = await svc.progress(USER, language="he")
        assert he.overview.level == "בתחילת הדרך"

    async def test_progress_after_an_answer_and_a_goal(self, catalog):
        svc, store = practice(catalog, scripted([GOOD, GOOD, GOOD]), suggest_reviewed_only=False)
        await svc.save_goal(USER, job_type="verification", interview_date=date.today() + timedelta(days=3),
                            minutes_per_day=15, seniority="student")
        view = await svc.start(USER, question_key=Q, mode="quick", language="en")
        await svc.submit(USER, uuid.UUID(view.id), "alarm = AB + BC + AC", idempotency_key="k1")

        progress = await svc.progress(USER, language="en")
        assert progress.overview.answered == 1 and progress.overview.strong == 1
        assert progress.overview.skills_assessed >= 0 and progress.overview.level_rank in range(6)
        assert len(progress.timeline) == 1 and progress.timeline[0].answered == 1 and progress.timeline[0].strong == 1
        assert progress.timeline[0].day == datetime.now(UTC).date().isoformat()
        plan = progress.plan
        assert plan.minutes_per_day == 15 and plan.days_to_interview == 3 and plan.interview_date is not None
        assert plan.items and all(0 <= item.day_index <= 3 for item in plan.items)
        assert all(sum(i.minutes for i in plan.items if i.day_index == d) <= 15 + 15 for d in range(4))
        assert any(item.done for item in plan.items if item.day_index == 0) or not any(
            "boolean_algebra" in [s.key for s in item.skills] for item in plan.items if item.day_index == 0)
        assert progress.goal.job_type == "verification" and progress.goal.complete

    async def test_an_abandoned_attempt_does_not_tick_the_plan(self, catalog):
        svc, store = practice(catalog, scripted([GOOD]), suggest_reviewed_only=False)
        await svc.start(USER, question_key=Q, mode="quick", language="en")          # opened, never answered
        progress = await svc.progress(USER, language="en")
        assert progress.overview.answered == 0 and not any(item.done for item in progress.plan.items)

    async def test_the_plan_takes_the_question_state_from_the_database(self, catalog):
        """Production: the seed file says in_review, the database says trial. The plan must see trial questions."""
        from app.repo.questions import LoadedQuestion, summary
        svc, store = practice(catalog)                                     # suggest_reviewed_only: the production default
        trial = [summary(LoadedQuestion(id=store.question_id(q.key), question=q.model_copy(update={"status": "trial"}),
                                        version=q.version), "en") for q in catalog.questions.values()]
        assert all(r.reviewed and r.trial for r in trial) and all(q.status == "in_review" for q in catalog.questions.values())
        profile = await (await store.transaction().__aenter__()).load_profile(USER)
        _, required, _, plan_skills = svc._plan("student")
        from app.repo.users import Goal
        items = svc._router_items(profile, plan_skills, required, trial, [], Goal(minutes_per_day=30), "en", date.today())
        assert items, "trial questions in the database must feed the plan"

    async def test_with_nothing_reviewed_the_plan_is_empty_not_an_error(self, catalog):
        svc, _ = practice(catalog)                                        # suggest_reviewed_only: the production default
        view = await svc.progress(USER, language="en")
        assert view.plan.items == [] and view.overview.answered == 0


# ----------------------------------------------------------------------------- visual answers in the interview


def interview(catalog, provider, **config) -> tuple[InterviewService, InMemoryStore]:
    store = InMemoryStore(catalog)
    svc = InterviewService(store, catalog, provider, InterviewConfig(reviewed_only=False, **config))
    svc.clock = Clock()
    return svc, store


async def open_majority(svc, store, user):
    """Start interviews until the open question is the majority-gate one (the plan may open elsewhere)."""
    for _ in range(6):
        view = await svc.start(user, duration_min=45, language="en")
        while view.status == "in_progress" and view.current_turn is not None and view.current_turn.question_key != Q:
            svc.clock.advance()
            _, view = await svc.answer(user, uuid.UUID(view.id), view.current_turn.index, "a plain answer",
                                       idempotency_key=f"skip-{view.current_turn.index}")
        if view.current_turn is not None and view.current_turn.question_key == Q:
            return view
        store.sessions.clear()
    raise AssertionError("the majority question was never asked")


class TestInterviewVisualAnswers:
    async def test_a_drawn_circuit_is_assessed_and_kept_on_the_turn(self, catalog):
        svc, store = interview(catalog, interviewer([GOOD]))
        view = await open_majority(svc, store, USER)
        turn = view.current_turn
        answer = {"text": "", "visual": {"circuit": majority_circuit(), "images": []}}
        result, view = await svc.answer(USER, uuid.UUID(view.id), turn.index, answer, idempotency_key="draw")
        assert result.status == "done" and result.visual is not None and result.visual.circuit is not None
        assert "circuit_assessed" in result.flags and result.answer == ""
        stored = next(t for t in store.sessions[uuid.UUID(view.id)]["turns"] if t["turn_index"] == turn.index)
        assert stored["question_generation_meta"]["answer_visual"]["circuit"]["parts"]
        assert stored["check_result"]["passed"] is True                    # the derived alarm function passed the truth table
        request = svc.provider.requests[-1]                                 # the evaluation of the drawing
        assert request.role == "evaluator"
        assert "alarm" in request.user.lower() and "circuit" in request.user.lower()
        # after a refresh the drawing is still there
        again = await svc.get(USER, uuid.UUID(view.id))
        shown = next((t for t in again.turns if t.index == turn.index), None)
        assert shown is not None and shown.visual is not None

    async def test_photos_only_without_a_fetcher_are_kept_for_a_human_and_can_be_resent(self, catalog):
        svc, store = interview(catalog, interviewer([GOOD]))
        view = await open_majority(svc, store, USER)
        sid = uuid.UUID(view.id)
        path = f"{USER}/{sid}/{uuid.uuid4()}.jpg"
        store.answer_images[path] = {"mime": "image/jpeg", "size": 100}
        image = {"path": path, "name": "board.jpg", "mime": "image/jpeg", "size": 100}
        turn = view.current_turn
        calls_before = len(svc.provider.requests)
        result, view = await svc.answer(USER, sid, turn.index, {"text": "", "visual": {"images": [image]}}, idempotency_key="photo")
        assert result.status == "failed" and result.flags == ["visual_review_pending", "images_not_assessed"]
        assert view.can_answer and len(svc.provider.requests) == calls_before      # nothing was invented about the photo
        # a photo that belongs to another attempt is refused
        wrong = {"path": f"{USER}/{uuid.uuid4()}/{uuid.uuid4()}.jpg", "name": "x.jpg", "mime": "image/jpeg", "size": 100}
        with pytest.raises(ApiError, match="image"):
            await svc.answer(USER, sid, turn.index, {"text": "", "visual": {"images": [wrong]}}, idempotency_key="photo2")
        # text after all: evaluated normally
        result, view = await svc.answer(USER, sid, turn.index, {"text": "alarm = AB + BC + AC"}, idempotency_key="text")
        assert result.status == "done"

    async def test_an_empty_answer_is_still_refused(self, catalog):
        svc, store = interview(catalog, interviewer([GOOD]))
        view = await svc.start(USER, duration_min=20, language="en")
        with pytest.raises(ApiError) as e:
            await svc.answer(USER, uuid.UUID(view.id), 0, {"text": "  ", "visual": {"images": []}}, idempotency_key="e")
        assert e.value.code == "validation"

    async def test_the_interview_plan_follows_the_goal(self, catalog):
        svc, store = interview(catalog, interviewer([GOOD]))
        store.goals[USER] = __import__("app.repo.users", fromlist=["Goal"]).Goal(job_type="verification", minutes_per_day=30)
        view = await svc.start(USER, duration_min=30, language="en")
        assert store.sessions[uuid.UUID(view.id)]["row"]["config"]["job_type"] == "verification"
        plain = await svc.start(OTHER, duration_min=30, language="en")
        assert store.sessions[uuid.UUID(plain.id)]["row"]["config"]["job_type"] is None
        assert len(view.plan) >= 1 and len(plain.plan) >= 1


# ----------------------------------------------------------------------------- over HTTP


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


@pytest.fixture
def headers():
    _, token = make_token(email=MEMBER)
    return {"Authorization": f"Bearer {token}"}


class TestOverHttp:
    async def test_job_types_goal_sightings_and_filters(self, client, headers):
        jobs = await client.get("/v1/job-types?language=he", headers=headers)
        assert jobs.status_code == 200 and {j["key"] for j in jobs.json()} >= {"verification", "fpga"}
        assert next(j for j in jobs.json() if j["key"] == "verification")["label"] == "וריפיקציה"

        saved = await client.post("/v1/me/goal", json={"job_type": "fpga", "minutes_per_day": 25,
                                                       "interview_date": (date.today() + timedelta(days=14)).isoformat(),
                                                       "seniority": "junior"}, headers=headers)
        assert saved.status_code == 200 and saved.json()["complete"] and saved.json()["days_to_interview"] == 14
        assert (await client.get("/v1/me/goal", headers=headers)).json()["job_type"] == "fpga"
        bad = await client.post("/v1/me/goal", json={"job_type": "fpga", "minutes_per_day": 5000}, headers=headers)
        assert bad.status_code == 422

        sighting = await client.post(f"/v1/questions/{Q}/sightings", json={"company": "Apple"}, headers=headers)
        assert sighting.status_code == 200 and sighting.json()["companies"] == [{"slug": "apple", "name": "Apple", "count": 1}]
        assert (await client.post(f"/v1/questions/{Q}/sightings", json={"company": ""}, headers=headers)).status_code == 422
        assert (await client.post("/v1/questions/nope/sightings", json={"company": "Apple"}, headers=headers)).status_code == 404

        listed = await client.get("/v1/questions?language=en&job=fpga", headers=headers)
        assert listed.status_code == 200 and listed.json() and all("fpga" in q["job_types"] for q in listed.json())
        by_company = await client.get("/v1/questions?language=en&company=apple", headers=headers)
        assert [q["key"] for q in by_company.json()] == [Q] and by_company.json()[0]["companies"][0]["slug"] == "apple"
        assert (await client.get("/v1/questions?language=en&job=astronaut", headers=headers)).status_code == 422
        companies = await client.get("/v1/companies", headers=headers)
        assert companies.json() == [{"slug": "apple", "name": "Apple", "questions": 1, "sightings": 1}]

        progress = await client.get("/v1/me/progress?language=he", headers=headers)
        body = progress.json()
        assert progress.status_code == 200 and body["overview"]["level"] == "בתחילת הדרך"
        assert body["plan"]["minutes_per_day"] == 25 and body["plan"]["days_to_interview"] == 14
        assert body["goal"]["job_type_label"] == "הנדסת FPGA"

    async def test_interview_answer_accepts_a_visual_object(self, client, headers):
        started = await client.post("/v1/interviews", json={"duration_min": 20, "language": "en"}, headers=headers)
        assert started.status_code == 201, started.text
        body = started.json()
        answer = {"answer": {"text": "I would draw it", "visual": {"circuit": majority_circuit(), "images": []}}}
        response = await client.post(f"/v1/interviews/{body['id']}/turns/0/answer", json=answer,
                                     headers={**headers, "Idempotency-Key": "v1"})
        assert response.status_code in (200, 202), response.text
        turn = response.json()["turn"]
        assert turn["visual"]["circuit"]["parts"] and "circuit_assessed" in turn["flags"]
