"""Plural career goals and broad learning use the same persisted selection across the product."""

import uuid
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy import JSON, Column, Date, Integer, MetaData, String, Table

from app.api.errors import ApiError
from app.api.v1.me import GoalRequest
from app.engine.catalog import load_catalog
from app.engine.job_selection import combined_job
from app.repo import users
from app.repo.users import Goal
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_interview_service import Clock, interviewer, run_to_the_end
from tests.test_practice_hardening import GOOD, SEEDS, scripted


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def practice(catalog):
    store = InMemoryStore(catalog)
    service = PracticeService(store, catalog, scripted([GOOD] * 5),
                              ServiceConfig(suggest_reviewed_only=False, feedback_in_background=False))
    return service, store


async def save(service, user, roles, **updates):
    return await service.save_goal(user, **{"job_type": None, "job_types": roles, "interview_date": None,
                                           "minutes_per_day": 37, "seniority": "junior", **updates})


async def test_repository_preserves_background_and_reads_legacy_and_plural_goals(monkeypatch):
    table = Table("user_profile", MetaData(), Column("id", String), Column("background", JSON),
                  Column("target_interview_date", Date), Column("available_minutes_per_day", Integer),
                  Column("seniority_self_assessed", String))

    async def profile_table(name):
        assert name == "user_profile"
        return table

    monkeypatch.setattr(users.db, "table", profile_table)

    class Connection:
        values = {"background": {"job_type": "software", "unrelated_setting": {"keep": True}},
                  "target_interview_date": None, "available_minutes_per_day": 30,
                  "seniority_self_assessed": "junior"}

        async def execute(self, statement):
            if statement.is_update:
                self.values.update({str(key): getattr(value, "value", None) for key, value in statement._values.items()})
            return SimpleNamespace(first=lambda: SimpleNamespace(**self.values),
                                   scalar_one_or_none=lambda: self.values["background"])

    connection = Connection()
    user = uuid.uuid4()
    legacy = await users.load_goal(connection, user)
    assert legacy.job_types == ["software"] and legacy.job_type == "software" and legacy.complete
    connection.values["background"]["job_types"] = []
    cleared = await users.load_goal(connection, user)
    assert cleared.job_types == [] and cleared.job_type is None and not cleared.complete
    await users.save_goal(connection, user, Goal(job_types=["software", "digital_design", "software"],
                                                minutes_per_day=37, seniority="mid"))
    loaded = await users.load_goal(connection, user)
    assert loaded.job_types == ["software", "digital_design"] and loaded.job_type == "software"
    assert loaded.selection == ("digital_design", "software") and loaded.minutes_per_day == 37
    assert connection.values["background"]["unrelated_setting"] == {"keep": True}
    await users.save_goal(connection, user, Goal(learning_mode="explore", job_type="software",
                                                interview_date=date.today(), minutes_per_day=22, seniority="student"))
    explore = await users.load_goal(connection, user)
    assert explore.complete and explore.job_types == [] and explore.job_type is None and explore.interview_date is None
    assert "job_type" not in connection.values["background"]
    assert connection.values["background"]["unrelated_setting"] == {"keep": True}


def test_role_union_includes_a_skill_if_any_selected_role_includes_it_without_duplicate_influence(catalog):
    roles = ["digital_design", "software"]
    merged = combined_job(catalog.job_types, roles)
    assert merged is not None
    for key in catalog.skills:
        jobs = [catalog.job_types[role] for role in roles]
        assert merged.excludes(key) == all(job.excludes(key) for job in jobs)
        assert merged.weight(key) == pytest.approx(sum(job.weight(key) for job in jobs) / len(jobs))
    assert merged == combined_job(catalog.job_types, [*reversed(roles), "software"])
    assert combined_job(catalog.job_types, []) is None


async def test_multi_role_save_labels_program_context_and_manual_minutes_survive_reload(catalog):
    service, store = practice(catalog)
    user = uuid.uuid4()
    result = await save(service, user, ["software", "digital_design", "software"], language="he")
    assert result.complete and result.job_types == ["software", "digital_design"]
    assert result.job_type == "software" and result.minutes_per_day == 37
    assert len(result.job_type_labels) == 2 and result.interview_date is None
    assert (await service.get_goal(user, language="he")) == result
    program = await service.program(user, language="en")
    assert program.goal_complete and program.plan.minutes_per_day == 37 and program.plan.interview_date is None
    expected = set(service._plan("junior", "software")[0]) | set(service._plan("junior", "digital_design")[0])
    assert set(service._plan("junior", store.goals[user].selection)[0]) == expected
    opened = await service.start(user, question_key="example-count-set-bits", mode="quick", language="en")
    attempt, *_ = await service._load(user, uuid.UUID(opened.id))
    assert attempt.ctx.job_types == ("digital_design", "software")
    assert {q.key for q in service._fitting(list(catalog.questions.values()), attempt.ctx.job_types)} == {
        q.key for q in catalog.questions.values() if any(catalog.job_types[role].fits(q) for role in result.job_types)}


async def test_role_and_mode_changes_rebuild_program_and_explore_is_a_complete_broad_goal(catalog):
    service, store = practice(catalog)
    user = uuid.uuid4()
    await save(service, user, ["software"])
    await service.program(user)
    first = store.plans[user].id
    await save(service, user, ["software", "digital_design"])
    await service.program(user)
    assert store.plans[user].id != first
    second = store.plans[user].id
    result = await save(service, user, [], learning_mode="explore", interview_date=date.today() + timedelta(days=12))
    assert result.complete and result.learning_mode == "explore"
    assert result.job_types == [] and result.job_type is None and result.interview_date is None
    broad = await service.program(user)
    assert broad.goal_complete and broad.plan.items and broad.plan.days_to_interview is None
    assert store.plans[user].id != second
    assert service._plan("junior", store.goals[user].selection) == service._plan("junior", None)
    assert not Goal(learning_mode="explore", minutes_per_day=30).complete
    assert not Goal(job_type="software", minutes_per_day=0).complete
    result = await save(service, user, ["fpga"])
    assert result.learning_mode == "targeted" and result.job_type == "fpga"


@pytest.mark.parametrize("updates", [{"job_types": ["software", "astronaut"]}, {"learning_mode": "other"},
                                    {"minutes_per_day": 4}, {"minutes_per_day": 601}, {"minutes_per_day": 30.5},
                                    {"minutes_per_day": True}, {"job_types": "software"}])
async def test_invalid_goal_options_fail_without_overwriting_saved_goal(catalog, updates):
    service, store = practice(catalog)
    user = uuid.uuid4()
    await save(service, user, ["software"])
    before = store.goals[user]
    with pytest.raises(ApiError, match="job|learning_mode|minutes_per_day"):
        await save(service, user, ["software"], **updates)
    assert store.goals[user] == before


@pytest.mark.parametrize("payload", [{"minutes_per_day": value} for value in (4, 601, 30.5, True)] +
                         [{"learning_mode": "other"}, {"job_types": ["x" * 41]}, {"job_types": "software"}])
def test_http_schema_rejects_malformed_values_instead_of_coercing_minutes(payload):
    with pytest.raises(ValidationError):
        GoalRequest.model_validate(payload)


async def test_interview_freezes_role_union_when_profile_changes_and_legacy_config_still_works(catalog, monkeypatch):
    service, store = practice(catalog)
    user = uuid.uuid4()
    await save(service, user, ["digital_design", "software"])
    interview = InterviewService(store, catalog, interviewer([GOOD]), InterviewConfig(reviewed_only=False, narrative=False))
    interview.clock = Clock(step_min=10)
    view = await interview.start(user, duration_min=20, language="en")
    config = store.sessions[uuid.UUID(view.id)]["row"]["config"]
    assert config["job_types"] == ["digital_design", "software"]
    await save(service, user, ["embedded_firmware"])
    selections = []
    original = interview._pool_for

    async def track(language, selection):
        selections.append(selection)
        return await original(language, selection)

    monkeypatch.setattr(interview, "_pool_for", track)
    completed, asked = await run_to_the_end(interview, user, view)
    assert completed.status == "completed" and asked and selections
    assert all(selection == config["job_types"] for selection in selections)
    assert all(any(catalog.job_types[role].fits(catalog.questions[key]) for role in config["job_types"]) for key in asked)
    assert interview._session_selection({"job_type": "software"}) == "software"
    assert interview._session_selection({"job_type": "software", "job_types": []}) == []
