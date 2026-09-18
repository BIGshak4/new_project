"""Data_Models §6.3 worked example: Senior Design Verification Engineer at Example
Semiconductor Co., 45 minutes, company weight share 0.30."""

import pytest

from app.engine.plan import company_rows_for_role, merge_skill_sets
from app.schemas.engine import AssessmentMode, CompanySkillRow, Importance, SkillSource


@pytest.fixture
def merged(catalog, dv_role_rows, semi_company_rows):
    plan = merge_skill_sets(role_rows=dv_role_rows, company_rows=semi_company_rows, focus_skill_keys=[],
                            company_weight_share=0.30, seniority="senior", planned_duration_min=45,
                            catalog=catalog)
    return {s.key: s for s in plan}


@pytest.mark.parametrize("key,source,combined,required,mode,turns", [
    ("debugging_methodology", SkillSource.ROLE_AND_COMPANY, 0.145, 5, AssessmentMode.QUESTIONED, 4),
    ("sv_assertions", SkillSource.ROLE_AND_COMPANY, 0.128, 4, AssessmentMode.QUESTIONED, 3),
    ("uvm_sequences", SkillSource.ROLE, 0.098, 4, AssessmentMode.QUESTIONED, 2),
    ("risk_awareness", SkillSource.COMPANY, 0.090, 3, AssessmentMode.OBSERVED, 0),
    ("uvm_scoreboard_monitor", SkillSource.ROLE, 0.084, 4, AssessmentMode.QUESTIONED, 2),
    ("formal_verification", SkillSource.COMPANY, 0.060, 3, AssessmentMode.QUESTIONED, 2),
    ("ownership", SkillSource.COMPANY, 0.045, 3, AssessmentMode.QUESTIONED, 1),
])
def test_spec_table_rows(merged, key, source, combined, required, mode, turns):
    skill = merged[key]
    assert skill.source == source
    assert skill.combined_weight == pytest.approx(combined, abs=5e-4)
    assert skill.required_level == required
    assert skill.assessment_mode == mode
    assert skill.planned_turns == turns


def test_weights_sum_to_one(merged):
    assert sum(s.combined_weight for s in merged.values()) == pytest.approx(1.0, abs=1e-3)


def test_required_level_is_clamped_to_five(catalog, dv_role_rows, semi_company_rows):
    plan = merge_skill_sets(role_rows=dv_role_rows, company_rows=semi_company_rows, focus_skill_keys=[],
                            company_weight_share=0.30, seniority="principal", planned_duration_min=45,
                            catalog=catalog)
    assert next(s for s in plan if s.key == "debugging_methodology").required_level == 5     # 5 + 1, clamped


def test_importance_is_the_higher_of_the_two(merged):
    assert merged["sv_assertions"].importance == Importance.CORE        # role core, company important


def test_core_skills_get_at_least_two_turns(merged):
    for skill in merged.values():
        if skill.importance == Importance.CORE and skill.assessment_mode == AssessmentMode.QUESTIONED:
            assert skill.planned_turns >= 2


def test_priority_core_first_and_prerequisites_before_dependents(merged):
    ranked = sorted(merged.values(), key=lambda s: s.priority_rank)
    first_non_core = next(i for i, s in enumerate(ranked) if s.importance != Importance.CORE)
    assert all(s.importance != Importance.CORE for s in ranked[first_non_core:])
    assert merged["fifo_verification"].priority_rank < merged["ooo_scoreboard"].priority_rank


def test_user_focus_adds_weight_and_renormalizes(catalog, dv_role_rows, semi_company_rows, merged):
    plan = merge_skill_sets(role_rows=dv_role_rows, company_rows=semi_company_rows,
                            focus_skill_keys=["ooo_scoreboard"], company_weight_share=0.30, seniority="senior",
                            planned_duration_min=45, catalog=catalog)
    by_key = {s.key: s for s in plan}
    assert by_key["ooo_scoreboard"].in_user_focus
    assert by_key["ooo_scoreboard"].combined_weight == pytest.approx((0.07 + 0.10) / 1.10, abs=5e-4)
    assert by_key["ooo_scoreboard"].planned_turns > merged["ooo_scoreboard"].planned_turns
    assert sum(s.combined_weight for s in plan) == pytest.approx(1.0, abs=1e-3)


def test_focus_skill_outside_the_plan_is_added(catalog, dv_role_rows):
    plan = merge_skill_sets(role_rows=dv_role_rows, company_rows=[], focus_skill_keys=["formal_verification"],
                            company_weight_share=0.0, seniority="junior", planned_duration_min=30, catalog=catalog)
    added = next(s for s in plan if s.key == "formal_verification")
    assert added.source == SkillSource.USER_FOCUS and added.in_user_focus


def test_generic_company_uses_the_role_set_alone(catalog, dv_role_rows):
    plan = merge_skill_sets(role_rows=dv_role_rows, company_rows=[], focus_skill_keys=[],
                            company_weight_share=0.30, seniority="junior", planned_duration_min=45, catalog=catalog)
    by_key = {s.key: s for s in plan}
    assert by_key["sv_assertions"].combined_weight == pytest.approx(0.14, abs=1e-4)
    assert all(s.source == SkillSource.ROLE for s in plan)
    assert by_key["sv_assertions"].required_level == 2


def test_company_scope_filter():
    rows = [
        CompanySkillRow(skill="a", weight=1, importance=Importance.CORE),
        CompanySkillRow(skill="b", weight=1, importance=Importance.CORE, scope="family", scope_family="software"),
        CompanySkillRow(skill="c", weight=1, importance=Importance.CORE, scope="family", scope_family="hardware"),
        CompanySkillRow(skill="d", weight=1, importance=Importance.CORE, scope="role", scope_role="other-role"),
        CompanySkillRow(skill="e", weight=1, importance=Importance.CORE, scope="role", scope_role="dv"),
    ]
    assert [r.skill for r in company_rows_for_role(rows, role_slug="dv", role_family="hardware")] == ["a", "c", "e"]


def test_student_seniority_falls_back_to_nearest_listed_level(catalog, dv_role_rows):
    plan = merge_skill_sets(role_rows=dv_role_rows, company_rows=[], focus_skill_keys=[],
                            company_weight_share=0.0, seniority="student", planned_duration_min=30, catalog=catalog)
    assert next(s for s in plan if s.key == "sv_assertions").required_level == 2      # junior's level
