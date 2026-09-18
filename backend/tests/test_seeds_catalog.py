"""The real seed files must load, validate, and produce a usable plan."""

import json
from pathlib import Path

import pytest

from app.engine.catalog import CatalogError, load_catalog
from app.engine.plan import merge_skill_sets
from app.schemas.engine import AssessmentMode

SEEDS = Path(__file__).resolve().parent.parent / "seeds"


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def test_seed_files_are_valid(catalog):
    assert len(catalog.domains) == 6
    assert len(catalog.leaf_skills) >= 30
    assert "digital-hardware-engineer" in catalog.roles and "generic" in catalog.companies


def test_the_six_launch_subjects_match_the_database_seed(catalog):
    assert set(catalog.domains) == {"digital_fundamentals", "sequential_logic", "fsms", "relevant_programming",
                                    "reasoning", "projects_behavioral"}


def test_every_skill_has_a_five_level_rubric_and_a_parent(catalog):
    for skill in catalog.leaf_skills.values():
        assert set(skill.proficiency_rubric) == {"1", "2", "3", "4", "5"}, skill.key
        assert skill.subject in catalog.domains, skill.key


def test_role_weights_sum_to_one_and_cover_student_and_junior(catalog):
    role = catalog.roles["digital-hardware-engineer"]
    assert sum(r.weight for r in role.skill_set) == pytest.approx(1.0, abs=1e-6)
    assert set(role.seniority_profiles) == {"student", "junior"}
    assert all({"student", "junior"} <= set(r.required_level) for r in role.skill_set)


def test_student_plan_for_the_launch_role(catalog):
    role, company = catalog.roles["digital-hardware-engineer"], catalog.companies["generic"]
    plan = merge_skill_sets(role_rows=role.skill_set, company_rows=company.skill_set, focus_skill_keys=[],
                            company_weight_share=company.company_weight_share, seniority="student",
                            planned_duration_min=45, catalog=catalog.leaf_skills)
    assert sum(s.combined_weight for s in plan) == pytest.approx(1.0, abs=1e-3)
    assert {s.subject for s in plan} <= set(catalog.domains)
    observed = [s for s in plan if s.assessment_mode == AssessmentMode.OBSERVED]
    assert {s.key for s in observed} == {"structured_communication", "tradeoff_reasoning"}
    assert all(s.planned_turns == 0 for s in observed)
    by_key = {s.key: s for s in plan}
    assert by_key["fsm_state_tables"].priority_rank < by_key["fsm_sequence_detectors"].priority_rank


def test_golden_questions_are_bilingual_with_three_hints(catalog):
    assert len(catalog.questions) >= 3
    for question in catalog.questions.values():
        assert set(question.translations) == {"en", "he"}, question.key
        for text in question.translations.values():
            assert len(text.hints) == 3 and text.reference_solution and text.requirements


def test_nothing_is_published_without_review(catalog):
    for question in catalog.questions.values():
        if question.status == "published":
            assert question.reviewed_by and question.reuse_status in ("permitted", "attribution_required")


def test_tips_are_bilingual_and_never_informational(catalog):
    for tip in catalog.tips.values():
        assert {"en", "he"} <= set(tip.templates), tip.key
        assert "Next time, try" in tip.templates["en"], tip.key       # actionability is the contract (§6.4)


def _copy_seeds(tmp_path: Path) -> Path:
    import shutil
    target = tmp_path / "seeds"
    shutil.copytree(SEEDS, target)
    return target


def test_loader_reports_every_problem_at_once(tmp_path):
    seeds = _copy_seeds(tmp_path)
    role_path = seeds / "roles" / "digital-hardware-engineer.json"
    role = json.loads(role_path.read_text(encoding="utf-8"))
    role["skill_set"][0]["skill"] = "no_such_skill"
    role["skill_set"][1]["weight"] = 0.5
    role_path.write_text(json.dumps(role), encoding="utf-8")
    with pytest.raises(CatalogError) as raised:
        load_catalog(seeds)
    text = "\n".join(raised.value.problems)
    assert "no_such_skill" in text and "weights sum to" in text


def test_a_broken_deterministic_check_is_caught_by_its_self_test(tmp_path):
    seeds = _copy_seeds(tmp_path)
    path = seeds / "questions" / "example_bank.json"
    questions = json.loads(path.read_text(encoding="utf-8"))
    majority = next(q for q in questions if q["key"] == "example-sensor-majority")
    majority["deterministic_check"]["spec"]["minterms"] = [3, 5, 6]          # wrong: drops 111
    path.write_text(json.dumps(questions, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(CatalogError) as raised:
        load_catalog(seeds)
    assert any("self-test" in p for p in raised.value.problems)


def test_prerequisite_cycle_is_rejected(tmp_path):
    seeds = _copy_seeds(tmp_path)
    path = seeds / "skills" / "digital_hardware.json"
    skills = json.loads(path.read_text(encoding="utf-8"))
    next(s for s in skills if s["key"] == "latches_flip_flops")["prerequisites"] = ["counters"]
    path.write_text(json.dumps(skills, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(CatalogError) as raised:
        load_catalog(seeds)
    assert any("cycle" in p for p in raised.value.problems)


def test_company_claims_need_dated_evidence(tmp_path):
    seeds = _copy_seeds(tmp_path)
    (seeds / "companies" / "example-semi.json").write_text(json.dumps({
        "slug": "example-semi", "display_name": "Example Semi", "company_weight_share": 0.3,
        "skill_set": [{"skill": "setup_hold_timing", "weight": 1.0, "importance": "core", "required_level_offset": 1}],
        "evidence": []}), encoding="utf-8")
    with pytest.raises(CatalogError) as raised:
        load_catalog(seeds)
    assert any("cites no evidence" in p for p in raised.value.problems)


# ----------------------------------------------------------------------------- Harel's bank


def test_example_bank_is_generated_from_harels_questions_and_the_enrichment():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, "scripts/build_example_bank.py", "--check"], capture_output=True, text=True,
                            cwd=Path(__file__).resolve().parent.parent)
    assert result.returncode == 0, result.stdout + result.stderr


def test_every_bank_question_keeps_harels_key_text_and_hint(catalog):
    source = json.loads((SEEDS.parent.parent / "example_question" / "questions.json").read_text(encoding="utf-8"))
    assert len(catalog.questions) == 30
    for item in source["questions"]:
        question = catalog.questions[f"example-{item['key']}"]
        for language in ("en", "he"):
            text = question.text(language)
            assert text.prompt == item["translations"][language]["prompt"]
            assert text.reference_solution == item["translations"][language]["reference_solution"]
            assert item["translations"][language]["hint"] in text.hints and len(text.hints) == 3
        assert question.assets["collection"] == "jobrun_example_v1" and question.assets["source_id"] == item["id"]
        assert question.status == "in_review" and not question.languages_ready()


def test_shared_code_travels_with_the_prompt(catalog):
    question = catalog.questions["example-nonblocking-pipeline-trace"]
    assert "always @(posedge clk)" in question.prompt_with_code("he")
    assert "always @(posedge clk)" not in question.text("he").prompt          # Harel's text is untouched


def test_bank_coverage_of_the_launch_role(catalog):
    from app.engine import bank
    role = catalog.roles["digital-hardware-engineer"]
    coverage = bank.coverage_by_skill(list(catalog.questions.values()), language="he", allow_in_review=True,
                                      require_parity=False)
    covered = [r.skill for r in role.skill_set if r.skill in coverage]
    uncovered = [r.skill for r in role.skill_set if r.skill not in coverage and r.assessment_mode is None]
    assert len(covered) >= 14, covered
    # known gaps, to be filled by the next content batch (not a failure, but visible in the test output)
    print("\nrole skills without a bank question yet:", uncovered)
