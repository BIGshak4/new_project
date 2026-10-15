"""Task 8 (Harel's allocation, Shaked: "it should be hidden", 2026-10-15): a skill at emphasis 0 is not part of a job
type. It leaves the plan, and its questions are hidden from the job-filtered library, the suggestion after an answer,
the program, readiness and the interview. Switching the job type brings them back. In-memory store, scripted model."""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from app.engine.catalog import load_catalog
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_interview_service import Clock, interviewer, run_to_the_end
from tests.test_practice_hardening import GOOD, SEEDS, WEAK, scripted
from tests.test_program import TODAY

USER = uuid.uuid4()
ROLE = "digital-hardware-engineer"

# examples both ways, by key: what each track must show and must hide
SHOWN = {"embedded_firmware": "example-count-set-bits",                   # bit manipulation, emphasised 1.6
         "digital_design": "example-nonblocking-pipeline-trace",           # HDL, emphasised 1.4
         "software": "example-count-set-bits",
         "fpga": "example-setup-hold-calculation"}
HIDDEN = {"embedded_firmware": "example-nonblocking-pipeline-trace",      # HDL coding is not firmware work
          "digital_design": "example-pair-sum-indices",                    # a data-structure puzzle is software screening
          "software": "example-setup-hold-calculation",                    # timing closure is hardware design
          "fpga": "example-pair-sum-indices"}


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def practice(catalog, provider=None) -> tuple[PracticeService, InMemoryStore]:
    store = InMemoryStore(catalog)
    return PracticeService(store, catalog, provider or scripted([GOOD, GOOD, GOOD]),
                           ServiceConfig(suggest_reviewed_only=False)), store


async def goal(svc, job_type, minutes=60):
    await svc.save_goal(USER, job_type=job_type, interview_date=TODAY + timedelta(days=10), minutes_per_day=minutes,
                        seniority="student")


class TestTheRule:
    def test_zero_means_not_part_of_the_job_type(self, catalog):
        embedded, student = catalog.job_types["embedded_firmware"], catalog.job_types["student_general"]
        assert embedded.excludes("hdl_sequential_coding") and not embedded.excludes("bit_manipulation")
        assert embedded.excludes("no_such_skill") is False                     # unlisted: emphasis 1.0, never hidden
        assert embedded.excluded_skills == ["hdl_blocking_nonblocking", "hdl_combinational_coding", "hdl_sequential_coding",
                                            "setup_hold_timing", "testbench_basics", "universal_gates"]
        assert student.excluded_skills == [] and catalog.job_types["verification"].excluded_skills == []
        role_skills = {r.skill for r in catalog.roles[ROLE].skill_set}
        for job in catalog.job_types.values():
            assert all(k in catalog.skills for k in job.excluded_skills)
            assert not (set(job.excluded_skills) & {"debugging_methodology", "structured_communication"})
        assert role_skills & set(catalog.job_types["software"].excluded_skills)   # the zeros reach the plan's skills

    def test_a_question_fits_by_its_primary_skill_not_a_secondary_link(self, catalog):
        embedded = catalog.job_types["embedded_firmware"]
        shift = catalog.questions["example-load-and-serial-shift"]              # registers first, HDL sequential second
        assert {link.skill for link in shift.skills} & set(embedded.excluded_skills)
        assert embedded.fits(shift)                                              # the side link does not hide it
        assert not embedded.fits(catalog.questions["example-nonblocking-pipeline-trace"])


class TestTheSeedLoader:
    """Review findings 2026-10-15: `false` or "0" must not become an exclusion; a job type must leave something."""

    def test_emphasis_takes_numbers_only(self):
        from pydantic import ValidationError

        from app.schemas.bank import JobType
        for bad in (False, True, "0", "1.5"):
            with pytest.raises(ValidationError):
                JobType(key="x", label={"en": "x"}, emphasis={"counters": bad})
        assert JobType(key="x", label={"en": "x"}, emphasis={"counters": 0}).excludes("counters")
        assert JobType(key="x", label={"en": "x"}, emphasis={"counters": 1.5}).weight("counters") == 1.5

    def test_a_job_type_that_excludes_every_role_skill_is_refused(self, tmp_path, catalog):
        import json
        import shutil

        from app.engine.catalog import CatalogError, load_catalog
        seeds = tmp_path / "seeds"
        shutil.copytree(SEEDS, seeds)
        jobs = json.loads((seeds / "job_types.json").read_text(encoding="utf-8"))
        role_skills = [r.skill for r in catalog.roles[ROLE].skill_set]
        jobs.append({"key": "nothing_left", "label": {"en": "Nothing"}, "emphasis": {k: 0 for k in role_skills}})
        (seeds / "job_types.json").write_text(json.dumps(jobs), encoding="utf-8")
        with pytest.raises(CatalogError, match="excludes every skill"):
            load_catalog(seeds)


class TestTheLibrary:
    async def test_examples_both_ways(self, catalog):
        svc, _ = practice(catalog)
        for job_type in SHOWN:
            keys = {r.key for r in await svc.list_questions(language="en", job=job_type)}
            assert SHOWN[job_type] in keys, job_type
            assert HIDDEN[job_type] not in keys, job_type
        everything = {r.key for r in await svc.list_questions(language="en")}
        assert set(HIDDEN.values()) <= everything                                # the unfiltered library shows all

    async def test_counts_the_filtered_library_is_everything_minus_the_excluded_primary_skills(self, catalog):
        svc, _ = practice(catalog)
        everything = await svc.list_questions(language="en")
        expected_hidden = {"embedded_firmware": 5, "software": 20, "digital_design": 13, "fpga": 13, "verification": 0,
                           "student_general": 0}                                 # the bank of 2026-10-15 (67 questions)
        for key, job in catalog.job_types.items():
            hidden = {r.key for r in everything if job.excludes(catalog.questions[r.key].primary_skill)}
            rows = await svc.list_questions(language="en", job=key)
            assert len(rows) == len(everything) - len(hidden), key
            assert not ({r.key for r in rows} & hidden), key
            assert all(key in r.job_types and r.relevance is not None for r in rows), key
            if len(everything) == 67:
                assert len(hidden) == expected_hidden[key], key

    async def test_the_job_tags_on_a_question_use_the_same_rule(self, catalog):
        svc, _ = practice(catalog)
        by_key = {r.key: r for r in await svc.list_questions(language="en")}
        assert "embedded_firmware" not in by_key["example-nonblocking-pipeline-trace"].job_types
        assert "digital_design" in by_key["example-nonblocking-pipeline-trace"].job_types
        counters = [r for r in by_key.values() if catalog.questions[r.key].primary_skill == "counters"]
        assert counters and all("embedded_firmware" in r.job_types for r in counters)   # 0.9 for embedded: shown, low
        assert "software" not in by_key["example-setup-hold-calculation"].job_types


class TestThePlanAndTheProgram:
    def test_the_plan_drops_excluded_skills_and_stays_normalised(self, catalog):
        svc, _ = practice(catalog)
        _, base, ceiling, base_plan = svc._plan("student")
        _, weights, ceiling2, plan = svc._plan("student", "embedded_firmware")
        excluded = set(catalog.job_types["embedded_firmware"].excluded_skills)
        assert ceiling == ceiling2
        assert {p.key for p in plan} == {p.key for p in base_plan} - excluded
        assert not (set(weights) & excluded)
        assert abs(sum(weights.values()) - sum(base.values())) < 1e-3          # weights are rounded to 4 places
        assert "hdl_sequential_coding" in {p.key for p in svc._plan("student", "digital_design")[3]}

    async def test_a_week_for_an_embedded_goal_never_plans_an_excluded_skill_and_the_switch_brings_them_back(self, catalog):
        svc, store = practice(catalog)
        await goal(svc, "embedded_firmware")
        excluded = set(catalog.job_types["embedded_firmware"].excluded_skills)
        view = await svc.program(USER, language="en")
        assert view.plan.items
        assert not ({s.key for i in view.plan.items for s in i.skills} & excluded)
        readiness = await svc.readiness(USER, language="en")
        assert not ({r.key for r in readiness.skills} & excluded)
        assert not any(catalog.job_types["embedded_firmware"].excludes(catalog.questions[q.key].primary_skill)
                       for q in readiness.next_questions)
        await goal(svc, "digital_design")                                        # re-plans at once
        again = await svc.readiness(USER, language="en")
        assert "hdl_sequential_coding" in {r.key for r in again.skills}
        rebuilt = await svc.program(USER, language="en")
        assert [i.id for i in rebuilt.plan.items] != [i.id for i in view.plan.items]   # re-planned for the new job type

    async def test_a_plan_start_opens_a_fitting_question(self, catalog):
        svc, _ = practice(catalog, scripted([GOOD] * 30))
        await goal(svc, "software")
        job = catalog.job_types["software"]
        opened = 0
        for _ in range(3):
            started = await svc.start_program_item(USER, language="en")
            if started.kind != "attempt":
                break
            opened += 1
            assert job.fits(catalog.questions[started.attempt.question.key])
            await svc.submit(USER, uuid.UUID(started.attempt.id), "an answer", idempotency_key=str(uuid.uuid4()))
        assert opened >= 1


class TestTheSuggestion:
    async def test_after_a_weak_answer_on_a_hidden_question_the_coach_does_not_stay_on_its_skill(self, catalog):
        """Opened from the unfiltered library: a software candidate answers a timing question badly. Without the job
        filter the coach would reinforce the same skill with the other timing question; with it, it moves on."""
        svc, _ = practice(catalog, scripted([WEAK, WEAK, WEAK]))
        await goal(svc, "software")
        attempt = await svc.start(USER, question_key="example-setup-hold-calculation", language="en")
        _, attempt = await svc.submit(USER, uuid.UUID(attempt.id), "the hold time is the clock period", idempotency_key="k1")
        assert attempt.next_question is not None
        picked = catalog.questions[attempt.next_question.key]
        assert catalog.job_types["software"].fits(picked)
        assert picked.primary_skill != "setup_hold_timing"

    async def test_without_a_job_type_nothing_is_hidden(self, catalog):
        svc, _ = practice(catalog, scripted([WEAK, WEAK]))
        everything = list(catalog.questions.values())
        assert svc._fitting(everything, None) == everything
        assert svc._fitting(everything, "student_general") == everything
        assert svc._fitting(everything, "no-such-job") == everything              # unknown: ignored, never an error here
        attempt = await svc.start(USER, question_key="example-setup-hold-calculation", language="en")
        _, attempt = await svc.submit(USER, uuid.UUID(attempt.id), "the hold time is the clock period", idempotency_key="k1")
        assert attempt.next_question is not None                                  # the coach still has somewhere to go


class TestTheInterview:
    async def test_the_interview_plan_and_pool_follow_the_job_type(self, catalog):
        store = InMemoryStore(catalog)
        coach = PracticeService(store, catalog, scripted([GOOD]), ServiceConfig(suggest_reviewed_only=False))
        await goal(coach, "embedded_firmware")
        svc = InterviewService(store, catalog, interviewer([GOOD, WEAK]), InterviewConfig(reviewed_only=False))
        svc.clock = Clock()
        excluded = set(catalog.job_types["embedded_firmware"].excluded_skills)
        plan, _, _ = svc._plan("student", 30, "embedded_firmware")
        assert plan and not ({p.key for p in plan} & excluded)
        assert "hdl_sequential_coding" in {p.key for p in svc._plan("student", 30, "digital_design")[0]}
        view = await svc.start(USER, duration_min=30, language="en")
        view, asked = await run_to_the_end(svc, USER, view)
        assert view.status == "completed" and asked
        assert all(catalog.job_types["embedded_firmware"].fits(catalog.questions[k]) for k in asked)
        assert view.plan and not ({p.skill for p in view.plan} & excluded)
