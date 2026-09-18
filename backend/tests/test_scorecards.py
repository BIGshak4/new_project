"""Data_Models §7.2 fit formula and caps, §7.3 roll-up, §7.4 target fit."""

import pytest

from app.engine.scorecards import (
    AssessedSkill,
    PastAssessment,
    build_scorecard,
    roll_up_profile,
    target_fit,
)
from app.schemas.engine import EvidenceStatus, Importance

A, I_, N = EvidenceStatus.ASSESSED, EvidenceStatus.INSUFFICIENT, EvidenceStatus.NOT_ASSESSED


def skill(key, weight, required, level, *, importance=Importance.IMPORTANT, status=A, subject="s"):
    return AssessedSkill(key=key, weight=weight, importance=importance, required_level=required,
                         status=status, proficiency_level=level, subject=subject)


class TestFit:
    def test_weighted_formula(self):
        card = build_scorecard([skill("a", 0.6, 4, 4), skill("b", 0.4, 4, 2)])
        assert card.fit_score == pytest.approx(100 * (0.6 * 1.0 + 0.4 * 0.5))

    def test_exceeding_a_requirement_does_not_offset_a_gap(self):
        card = build_scorecard([skill("a", 0.5, 2, 5), skill("b", 0.5, 4, 2)])
        assert card.fit_score == 75.0

    def test_core_gap_of_one_level_caps_at_80(self):
        card = build_scorecard([skill("core", 0.1, 4, 3, importance=Importance.CORE), skill("b", 0.9, 3, 5)])
        assert card.fit_score == 80.0 and card.cap_applied == 80.0 and card.core_gaps == ["core"]

    def test_core_gap_of_two_levels_caps_at_60(self):
        """§4.10: debugging level 2 against required 5 caps company fit at 60%."""
        card = build_scorecard([skill("debugging", 0.25, 5, 2, importance=Importance.CORE), skill("b", 0.75, 3, 5)])
        assert card.fit_score == 60.0

    def test_cap_never_raises_a_low_score(self):
        card = build_scorecard([skill("core", 1.0, 5, 1, importance=Importance.CORE)])
        assert card.fit_score == 20.0 and card.cap_applied is None

    def test_non_core_gap_is_not_capped(self):
        card = build_scorecard([skill("a", 0.05, 5, 1), skill("b", 0.95, 3, 3)])
        assert card.fit_score > 80

    def test_insufficient_evidence_is_excluded_from_fit(self):
        card = build_scorecard([skill("a", 0.5, 4, 4), skill("b", 0.5, 4, 1, status=I_),
                                skill("c", 0.5, 4, None, status=N)])
        assert card.fit_score == 100.0
        assert (card.skills_total, card.skills_assessed, card.skills_meeting_requirement) == (3, 1, 1)

    def test_partial_evaluation_flag_below_sixty_percent_coverage(self):
        rows = [skill("a", 0.2, 3, 3)] + [skill(f"n{i}", 0.2, 3, None, status=N) for i in range(2)]
        assert build_scorecard(rows).partial_evaluation is True
        assert build_scorecard([skill("a", 0.5, 3, 3), skill("b", 0.5, 3, 3)]).partial_evaluation is False

    def test_nothing_assessed_gives_no_score_rather_than_zero(self):
        assert build_scorecard([skill("a", 1.0, 3, None, status=N)]).fit_score is None

    def test_top_strengths_and_domain_breakdown(self):
        card = build_scorecard([skill("a", 0.3, 2, 5, subject="x"), skill("b", 0.3, 3, 4, subject="x"),
                                skill("c", 0.4, 4, 2, subject="y")])
        assert card.top_strengths == ["a", "b"]
        assert card.domain_breakdown == {"x": 100.0, "y": 50.0}


class TestRollup:
    def test_single_assessment_is_new(self):
        out = roll_up_profile([PastAssessment(3, 2)])
        assert (out.proficiency_level, out.trend, out.assessments_count) == (3, "new", 1)

    def test_recency_and_evidence_weighting(self):
        out = roll_up_profile([PastAssessment(4, 3), PastAssessment(2, 3)])
        assert out.level_score == pytest.approx((3 * 4 + 3 * 0.7 * 2) / (3 + 2.1), abs=0.01)
        assert out.proficiency_level == 3

    def test_trends(self):
        assert roll_up_profile([PastAssessment(4, 2), PastAssessment(3, 2), PastAssessment(3, 2)]).trend == "improving"
        assert roll_up_profile([PastAssessment(2, 2), PastAssessment(3, 2), PastAssessment(3, 2)]).trend == "declining"
        assert roll_up_profile([PastAssessment(3, 2), PastAssessment(3, 2)]).trend == "stable"

    def test_empty(self):
        assert roll_up_profile([]) is None


def test_target_fit_counts_unknown_skills_as_unknown_not_zero(catalog, dv_role_rows):
    from app.engine.plan import merge_skill_sets
    plan = merge_skill_sets(role_rows=dv_role_rows, company_rows=[], focus_skill_keys=[], company_weight_share=0,
                            seniority="junior", planned_duration_min=45, catalog=catalog)
    fit = target_fit(plan, {"sv_assertions": 2, "uvm_sequences": 2})
    assert fit.fit_score == 100.0
    assert fit.known_coverage == pytest.approx(0.28, abs=0.01)
    assert "debugging_methodology" in fit.unknown_skills and fit.core_gaps == []
