"""A job type brings its own skills (Shaked, 2026-11-14: "when we choose a specific work type the backend doesn't give
the correct workflow until the interview according to the skills needed"). Until then a job type could only multiply
the hardware role's rows, so a software plan had no arrays or data structures, and a verification plan kept
testbenches at the bottom. In-memory store, scripted model."""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import timedelta

import pytest

from app.engine.catalog import CatalogError, load_catalog
from app.engine.job_selection import plan_rows
from app.schemas.bank import JobType
from app.schemas.engine import Importance, RoleSkillRow
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_interview_service import Clock, interviewer, run_to_the_end
from tests.test_practice_hardening import GOOD, SEEDS, scripted
from tests.test_program import TODAY

ROLE = "digital-hardware-engineer"
PUZZLES = "estimation_sanity_checks"          # the logic and estimation puzzles every track is asked
ANALOG = "prep-mosfet-structure-current-bias-model"      # filed under the puzzles skill, but no software interview asks it
HARDWARE_TRACKS = {"digital_design", "verification", "fpga", "embedded_firmware", "student_general"}
# what each track is about: the skills its first day must reach for a candidate nobody has measured yet
SIGNATURE = {"software": {"arrays_and_search", "basic_data_structures"},
             "embedded_firmware": {"bit_manipulation"},
             "verification": {"testbench_basics"}}


@pytest.fixture(scope="module")
def catalog():
    """The seed bank as production serves it: ASSESS_UNREVIEWED_QUESTIONS is on there (§5zx), so the intake's
    questions are assessable and the testbench and software skills have questions to plan. This module's own instance."""
    loaded = load_catalog(SEEDS)
    for question in loaded.questions.values():
        if question.assets.get("assessment_ready") is False:
            question.assets["assessment_ready"] = True
    return loaded


def row(skill, weight, importance="important", **levels) -> RoleSkillRow:
    return RoleSkillRow(skill=skill, weight=weight, importance=importance, required_level=levels or {"student": 2, "junior": 2})


ROLE_ROWS = [row("counters", 0.6, "core", student=2, junior=3), row("truth_tables", 0.4)]


def job(key, emphasis=None, skills=()) -> JobType:
    return JobType(key=key, label={"en": key}, emphasis=emphasis or {}, skills=list(skills))


def practice(catalog) -> tuple[PracticeService, InMemoryStore]:
    store = InMemoryStore(catalog)
    return PracticeService(store, catalog, scripted([GOOD] * 30), ServiceConfig(suggest_reviewed_only=False)), store


class TestTheRows:
    def test_without_a_job_type_the_role_is_used_as_is(self):
        jobs = {"plain": job("plain")}
        assert plan_rows(ROLE_ROWS, jobs, None) == ROLE_ROWS
        assert plan_rows(ROLE_ROWS, jobs, "no-such-job") == ROLE_ROWS              # unknown: ignored, never an error
        assert plan_rows(ROLE_ROWS, jobs, "plain") == ROLE_ROWS

    def test_an_own_skill_joins_and_emphasis_multiplies_it_like_any_other_row(self):
        jobs = {"sw": job("sw", {"arrays_and_search": 1.5, "truth_tables": 0}, [row("arrays_and_search", 0.2, "core")])}
        rows = {r.skill: r for r in plan_rows(ROLE_ROWS, jobs, "sw")}
        assert set(rows) == {"counters", "arrays_and_search"}                      # joined; the excluded one left
        assert rows["arrays_and_search"].weight == pytest.approx(0.3) and rows["arrays_and_search"].importance == Importance.CORE
        assert rows["counters"].weight == pytest.approx(0.6)

    def test_a_row_for_a_role_skill_replaces_the_roles_row_for_that_job_type_only(self):
        jobs = {"ver": job("ver", {"truth_tables": 2.0}, [row("truth_tables", 0.5, "core", student=3, junior=4)]),
                "plain": job("plain")}
        mine = {r.skill: r for r in plan_rows(ROLE_ROWS, jobs, "ver")}
        assert mine["truth_tables"].weight == pytest.approx(1.0) and mine["truth_tables"].importance == Importance.CORE
        assert mine["truth_tables"].required_level == {"student": 3, "junior": 4}
        assert [r.skill for r in plan_rows(ROLE_ROWS, jobs, "ver")] == ["counters", "truth_tables"]   # the role's order
        assert plan_rows(ROLE_ROWS, jobs, "plain") == ROLE_ROWS
        assert ROLE_ROWS[1].weight == 0.4 and ROLE_ROWS[1].importance == Importance.IMPORTANT     # the role is untouched

    def test_several_job_types_average_the_weight_and_keep_the_highest_demand(self):
        jobs = {"sw": job("sw", {"counters": 0}, [row("arrays_and_search", 0.2, "core", student=2, junior=3)]),
                "ver": job("ver", {}, [row("truth_tables", 0.5, "core", student=3, junior=2)])}
        rows = {r.skill: r for r in plan_rows(ROLE_ROWS, jobs, ["ver", "sw", "sw"])}
        assert set(rows) == {"counters", "truth_tables", "arrays_and_search"}      # excluded only when every one excludes
        assert rows["counters"].weight == pytest.approx(0.3)                       # 0.6 for one, absent for the other
        assert rows["arrays_and_search"].weight == pytest.approx(0.1)              # one job type's own: half the weight
        assert rows["truth_tables"].weight == pytest.approx(0.45)                  # (0.4 + 0.5) / 2
        assert rows["truth_tables"].importance == Importance.CORE
        assert rows["truth_tables"].required_level == {"student": 3, "junior": 2}
        assert plan_rows(ROLE_ROWS, jobs, ["sw", "ver"]) == plan_rows(ROLE_ROWS, jobs, ["ver", "sw", "sw"])


class TestTheSeeds:
    def test_every_skill_a_job_type_plays_up_is_in_its_plan(self, catalog):
        """The bug itself: an emphasis on a skill the plan lacks multiplies nothing and nobody notices."""
        role = catalog.roles[ROLE]
        for key, job_type in catalog.job_types.items():
            planned = {r.skill for r in plan_rows(role.skill_set, catalog.job_types, key)}
            ignored = sorted(skill for skill, value in job_type.emphasis.items() if value > 1.0 and skill not in planned)
            assert not ignored, f"{key} emphasises {ignored}, which its plan does not contain"

    def test_the_signature_skills_weigh_most_in_their_plan(self, catalog):
        svc, _ = practice(catalog)
        for key, signature in SIGNATURE.items():
            _, weights, _, plan = svc._plan("student", key)
            questioned = [p.key for p in plan if p.assessment_mode.value == "questioned"]
            heaviest = sorted(questioned, key=lambda k: -weights[k])[: len(signature)]
            assert set(heaviest) == signature, key
            assert all(p.importance == Importance.CORE for p in plan if p.key in signature), key
            assert abs(sum(weights.values()) - 1.0) < 1e-3, key

    def test_the_hardware_tracks_keep_the_roles_skills_plus_the_reasoning_puzzles(self, catalog):
        svc, _ = practice(catalog)
        base = {p.key for p in svc._plan("student")[3]}
        for key in ("digital_design", "fpga", "student_general"):
            assert {p.key for p in svc._plan("student", key)[3]} == base | {PUZZLES}, key
        assert not ({"arrays_and_search", "basic_data_structures", PUZZLES} & base)   # explore keeps the role as it is

    def test_the_reasoning_puzzles_are_in_every_job_types_plan(self, catalog):
        """68 questions that no plan scheduled: the skill was in no role and no job type (Shaked, 2026-11-14)."""
        svc, _ = practice(catalog)
        assert sum(q.primary_skill == PUZZLES for q in catalog.questions.values()) == 68
        for key in catalog.job_types:
            plan = {p.key: p for p in svc._plan("student", key)[3]}
            assert plan[PUZZLES].importance == Importance.IMPORTANT and plan[PUZZLES].combined_weight > 0, key

    def test_verification_plans_software_and_hardware_skills(self, catalog):
        svc, _ = practice(catalog)
        plan = {p.key for p in svc._plan("student", "verification")[3]}
        assert {"arrays_and_search", "basic_data_structures", "code_debugging"} <= plan       # the software side
        assert {"testbench_basics", "fsm_state_tables", "hdl_blocking_nonblocking"} <= plan    # the hardware side

    def test_software_does_not_treat_the_hardware_leftovers_as_core(self, catalog):
        svc, _ = practice(catalog)
        plan = {p.key: p for p in svc._plan("junior", "software")[3]}
        core = {k for k, p in plan.items() if p.importance == Importance.CORE}
        assert core == {"arrays_and_search", "basic_data_structures", "code_debugging"}
        assert plan["boolean_algebra"].required_level == 2 and plan["arrays_and_search"].required_level == 3


class TestAQuestionsOwnJobTypes:
    """`seeds/question_job_types.json`: a question that lists its job types follows the list, not its skill."""

    def test_a_listed_question_follows_its_list_and_the_others_their_skill(self, catalog):
        analog, puzzle = catalog.questions[ANALOG], catalog.questions["prep-twenty-five-horses"]
        assert analog.primary_skill == puzzle.primary_skill == PUZZLES
        assert {k for k, j in catalog.job_types.items() if j.fits(analog)} == HARDWARE_TRACKS
        assert {k for k, j in catalog.job_types.items() if j.fits(puzzle)} == set(catalog.job_types)   # every track
        hdl = catalog.questions["example-nonblocking-pipeline-trace"]
        assert not catalog.job_types["software"].fits(hdl) and catalog.job_types["fpga"].fits(hdl)     # by skill, as before

    def test_a_list_can_also_bring_a_question_into_a_job_type_that_excludes_its_skill(self):
        from types import SimpleNamespace
        embedded = job("embedded", {"hdl_sequential_coding": 0})
        embedded.questions.update({"kept": True, "dropped": False})
        assert embedded.fits(SimpleNamespace(key="kept", primary_skill="hdl_sequential_coding"))
        assert not embedded.fits(SimpleNamespace(key="dropped", primary_skill="counters"))
        assert not embedded.fits(SimpleNamespace(key="other", primary_skill="hdl_sequential_coding"))
        assert embedded.fits(SimpleNamespace(key="other", primary_skill="counters"))

    def test_with_several_job_types_a_listed_question_belongs_when_any_of_them_has_it(self, catalog):
        from app.engine.job_selection import combined_job
        analog = catalog.questions[ANALOG]
        assert combined_job(catalog.job_types, ["software", "fpga"]).fits(analog)
        assert not combined_job(catalog.job_types, ["software"]).fits(analog)

    async def test_the_library_tags_and_filters_by_the_list(self, catalog):
        svc, _ = practice(catalog)
        by_key = {r.key: r for r in await svc.list_questions(language="en")}
        assert set(by_key[ANALOG].job_types) == HARDWARE_TRACKS
        assert set(by_key["prep-twenty-five-horses"].job_types) == set(catalog.job_types)
        assert ANALOG not in {r.key for r in await svc.list_questions(language="en", job="software")}
        assert ANALOG in {r.key for r in await svc.list_questions(language="en", job="verification")}
        assert set((await svc.get_question(language="en", key=ANALOG)).job_types) == HARDWARE_TRACKS

    def test_the_loader_refuses_a_list_it_cannot_apply(self, tmp_path):
        seeds = tmp_path / "seeds"
        shutil.copytree(SEEDS, seeds)
        listed = json.loads((seeds / "question_job_types.json").read_text(encoding="utf-8"))
        listed.update({"no-such-question": ["software"], "prep-twenty-five-horses": ["software", "astronaut"],
                       "prep-josephus-forty-three": []})
        (seeds / "question_job_types.json").write_text(json.dumps(listed), encoding="utf-8")
        with pytest.raises(CatalogError) as caught:
            load_catalog(seeds)
        problems = "\n".join(caught.value.problems)
        for expected in ("no-such-question: unknown question", "prep-twenty-five-horses: unknown job type ['astronaut']",
                         "prep-josephus-forty-three: needs a list with at least one job type"):
            assert expected in problems, expected
        assert len(caught.value.problems) == 3


class TestTheProgramAndTheInterview:
    @pytest.mark.parametrize("job_type", sorted(SIGNATURE))
    async def test_the_first_day_of_a_new_candidate_starts_on_the_jobs_own_skills(self, catalog, job_type):
        svc, _ = practice(catalog)
        user = uuid.uuid4()
        await svc.save_goal(user, job_type=job_type, interview_date=TODAY + timedelta(days=10), minutes_per_day=30,
                            seniority="student")
        view = await svc.program(user, language="en")
        first_day = {s.key for item in view.plan.items if item.day_index == 0 for s in item.skills}
        assert first_day & SIGNATURE[job_type], (job_type, first_day)

    async def test_a_plan_start_for_software_opens_a_software_question(self, catalog):
        svc, _ = practice(catalog)
        user = uuid.uuid4()
        await svc.save_goal(user, job_type="software", interview_date=TODAY + timedelta(days=10), minutes_per_day=30,
                            seniority="student")
        started = await svc.start_program_item(user, language="en")
        assert started.kind == "attempt"
        assert catalog.questions[started.attempt.question.key].primary_skill in SIGNATURE["software"]

    async def test_readiness_lists_the_jobs_own_skills(self, catalog):
        svc, _ = practice(catalog)
        user = uuid.uuid4()
        await svc.save_goal(user, job_type="software", interview_date=None, minutes_per_day=30, seniority="student")
        readiness = await svc.readiness(user, language="en")
        assert SIGNATURE["software"] <= {r.key for r in readiness.skills}
        assert {r.key for r in readiness.skills[:2]} == SIGNATURE["software"]       # heaviest first

    async def test_the_software_interview_plans_and_asks_software_questions(self, catalog):
        store = InMemoryStore(catalog)
        coach = PracticeService(store, catalog, scripted([GOOD]), ServiceConfig(suggest_reviewed_only=False))
        user = uuid.uuid4()
        await coach.save_goal(user, job_type="software", interview_date=TODAY + timedelta(days=10), minutes_per_day=60,
                              seniority="student")
        svc = InterviewService(store, catalog, interviewer([GOOD]), InterviewConfig(reviewed_only=False))
        svc.clock = Clock()
        plan = {p.key: p for p in svc._plan("student", 30, "software")[0]}
        assert all(plan[k].planned_turns >= 2 for k in SIGNATURE["software"])
        view = await svc.start(user, duration_min=30, language="en")
        view, asked = await run_to_the_end(svc, user, view)
        assert view.status == "completed" and asked
        assert SIGNATURE["software"] & {catalog.questions[k].primary_skill for k in asked}
        assert SIGNATURE["software"] <= {p.skill for p in view.plan}


class TestTheSeedLoader:
    def test_own_rows_are_checked_like_a_roles(self, tmp_path, catalog):
        seeds = tmp_path / "seeds"
        shutil.copytree(SEEDS, seeds)
        jobs = json.loads((seeds / "job_types.json").read_text(encoding="utf-8"))
        good = {"skill": "arrays_and_search", "weight": 0.05, "importance": "core", "required_level": {"student": 2, "junior": 3}}
        jobs += [
            {"key": "typo", "label": {"en": "x"}, "skills": [{**good, "skill": "arrays_and_serach"}]},
            {"key": "twice", "label": {"en": "x"}, "skills": [good, good]},
            {"key": "heavy", "label": {"en": "x"}, "skills": [{**good, "weight": 1.6}]},
            {"key": "hidden", "label": {"en": "x"}, "emphasis": {"arrays_and_search": 0}, "skills": [good]},
            {"key": "level", "label": {"en": "x"}, "skills": [{**good, "required_level": {"student": 9, "junior": 3}}]},
            {"key": "no_junior", "label": {"en": "x"}, "skills": [{**good, "required_level": {"student": 2}}]},
        ]
        role_skills = [r.skill for r in catalog.roles[ROLE].skill_set]
        # every role skill excluded, but it brings its own: a plan is left, so this one is fine
        jobs.append({"key": "all_its_own", "label": {"en": "x"}, "emphasis": {k: 0 for k in role_skills}, "skills": [good]})
        (seeds / "job_types.json").write_text(json.dumps(jobs), encoding="utf-8")
        with pytest.raises(CatalogError) as caught:
            load_catalog(seeds)
        problems = "\n".join(caught.value.problems)
        for expected in ("typo/arrays_and_serach: not a leaf skill", "twice/arrays_and_search: listed twice",
                         "heavy/arrays_and_search: weight out of range", "hidden/arrays_and_search: its own skill is excluded",
                         "level/arrays_and_search: bad required level student=9",
                         "no_junior/arrays_and_search: no required level for ['junior']"):
            assert expected in problems, expected
        assert "all_its_own" not in problems
        assert len(caught.value.problems) == 6
