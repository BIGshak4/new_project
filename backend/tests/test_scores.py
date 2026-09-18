import pytest

from app.engine import scores
from app.schemas.engine import Archetype, Band, CheckResult, EvidenceStatus, ObservedState, SkillState
from tests.conftest import make_evaluation


class TestBands:
    """AI_Engine_Spec §3.1"""

    @pytest.mark.parametrize("correctness,depth,expected", [
        (0.75, 0.55, Band.STRONG), (0.90, 0.54, Band.PARTIAL), (0.74, 0.90, Band.PARTIAL),
        (0.45, 0.10, Band.PARTIAL), (0.44, 0.90, Band.WEAK),
    ])
    def test_thresholds(self, correctness, depth, expected):
        assert scores.classify_band(make_evaluation(correctness=correctness, depth=depth)) == expected

    def test_core_misconception_is_weak_even_when_correct(self):
        assert scores.classify_band(make_evaluation(0.9, 0.9), core_misconception=True) == Band.WEAK


class TestCheckAuthority:
    """§2.3: a failed check caps correctness at 0.4; a pass raises the floor to 0.6 but never sets 1.0."""

    def test_fail_caps(self):
        out = scores.apply_check_result(make_evaluation(correctness=0.9), CheckResult(type="truth_table", passed=False))
        assert out.correctness == 0.4

    def test_pass_floors_but_keeps_higher(self):
        passed = CheckResult(type="truth_table", passed=True)
        assert scores.apply_check_result(make_evaluation(correctness=0.3), passed).correctness == 0.6
        assert scores.apply_check_result(make_evaluation(correctness=0.85), passed).correctness == 0.85

    def test_unrunnable_check_changes_nothing(self):
        out = scores.apply_check_result(make_evaluation(correctness=0.3), CheckResult(type="sim", passed=None))
        assert out.correctness == 0.3


class TestEvidenceWeight:
    """§2.9"""

    @pytest.mark.parametrize("kwargs,expected", [
        (dict(mode="quick"), 0.3),
        (dict(mode="deep"), 1.0),
        (dict(mode="retention_check"), 1.2),
        (dict(mode="diagnostic"), 0.5),
        (dict(mode="deep", familiarity="seen_same"), 0.4),
        (dict(mode="deep", hint_level=3), 0.4),
        (dict(mode="deep", familiarity="seen_variation", hint_level=1, exposure_risk="medium"), 0.476),
        (dict(mode="retention_check", revealed_before_submit=True), 0.0),
    ])
    def test_products(self, kwargs, expected):
        assert scores.evidence_weight(**kwargs) == pytest.approx(expected)

    def test_never_exceeds_the_database_limit(self):
        assert scores.evidence_weight("retention_check") <= 1.2


class TestScoreUpdate:
    """§2.4"""

    def test_knowledge_formula(self):
        ev = make_evaluation(correctness=0.62, depth=0.50)
        out = scores.update_scores(k_old=50, c_old=50, evaluation=ev, difficulty=6, difficulty_ceiling=9,
                                   turns_on_skill=2)
        raw = 100 * (0.65 * 0.62 + 0.35 * 0.50)                 # 57.8
        factor = 0.6 + 0.4 * (6 / 9)
        assert out.k_after == pytest.approx(50 + 0.45 * factor * (raw - 50), abs=0.01)

    def test_first_two_turns_move_faster(self):
        ev = make_evaluation(correctness=0.9, depth=0.9)
        common = dict(k_old=40, c_old=50, evaluation=ev, difficulty=5, difficulty_ceiling=5)
        first = scores.update_scores(turns_on_skill=0, **common)
        later = scores.update_scores(turns_on_skill=2, **common)
        assert first.k_after > later.k_after

    def test_harder_questions_move_knowledge_more(self):
        ev = make_evaluation(correctness=0.9, depth=0.9)
        easy = scores.update_scores(k_old=40, c_old=50, evaluation=ev, difficulty=2, difficulty_ceiling=9, turns_on_skill=3)
        hard = scores.update_scores(k_old=40, c_old=50, evaluation=ev, difficulty=9, difficulty_ceiling=9, turns_on_skill=3)
        assert hard.k_after > easy.k_after

    def test_hint_penalty_is_eight_per_level(self):
        ev = make_evaluation()
        common = dict(k_old=50, c_old=50, evaluation=ev, difficulty=5, difficulty_ceiling=9, turns_on_skill=3,
                      latency_ms=10_000, revision_count=0)
        none = scores.update_scores(hint_level=0, **common)
        two = scores.update_scores(hint_level=2, **common)
        assert none.c_after - two.c_after == pytest.approx(0.35 * 16, abs=0.01)

    def test_zero_evidence_weight_changes_nothing(self):
        out = scores.update_scores(k_old=50, c_old=60, evaluation=make_evaluation(0.1, 0.1), difficulty=5,
                                   difficulty_ceiling=9, turns_on_skill=0, weight=0.0)
        assert (out.k_after, out.c_after) == (50, 60)

    def test_latency_norm(self):
        assert scores.latency_norm(30_000, difficulty=5) == 1.0
        assert scores.latency_norm(None, difficulty=5) == 0.5
        assert scores.latency_norm(10_000_000, difficulty=5) == 0.0


class TestPriors:
    """§2.5 order of preference"""

    def test_profile_beats_everything_and_decays(self):
        prior = scores.skill_prior(seniority="junior", profile_k=80, profile_c=70, days_since_assessed=30,
                                   prerequisite_ks=[10], subject_k=10)
        assert prior.source == "profile" and prior.k == pytest.approx(72.0)

    def test_prerequisites_minus_ten(self):
        prior = scores.skill_prior(seniority="junior", prerequisite_ks=[70, 50], subject_k=90)
        assert prior.source == "prerequisites" and prior.k == 50

    def test_subject_minus_five(self):
        assert scores.skill_prior(seniority="junior", subject_k=66).k == 61

    @pytest.mark.parametrize("seniority,k", [("junior", 40), ("mid", 55), ("senior", 65), ("staff", 72), ("principal", 78)])
    def test_seniority_defaults(self, seniority, k):
        assert scores.skill_prior(seniority=seniority).k == k

    def test_student_starts_below_junior(self):
        assert scores.skill_prior(seniority="student").k < 40

    def test_calibration_shifts_confidence_by_five(self):
        base = scores.skill_prior(seniority="junior").c
        assert scores.skill_prior(seniority="junior", calibration="overconfident").c == base - 5
        assert scores.skill_prior(seniority="junior", calibration="underconfident").c == base + 5


class TestLevels:
    """§2.6"""

    @pytest.mark.parametrize("difficulty,level", [(1, 1), (2, 1), (3, 2), (4, 2), (5, 3), (6, 3), (7, 4), (8, 4), (9, 5), (10, 5)])
    def test_ceiling_mapping(self, difficulty, level):
        assert scores.level_from_difficulty(difficulty) == level

    def _skill(self, turns, k=60.0):
        skill = SkillState(key="x", k=k, c=60.0)
        for difficulty, band, hint, level in turns:
            scores.record_turn(skill, difficulty=difficulty, band=band, evaluation=make_evaluation(level=level),
                               hint_level=hint, weight=1.0, core_misconception=False)
        return skill

    def test_formula(self):
        skill = self._skill([(5, Band.STRONG, 0, 3), (6, Band.STRONG, 0, 3), (7, Band.PARTIAL, 0, 3)], k=70)
        level, score = scores.questioned_level(skill)
        assert score == pytest.approx(0.5 * 3 + 0.35 * 3 + 0.15 * 3.5, abs=0.01)       # ceiling 6 -> 3
        assert level == 3

    def test_level3_hint_caps_one_below_that_difficulty(self):
        skill = self._skill([(7, Band.STRONG, 0, 4), (8, Band.STRONG, 0, 5), (8, Band.WEAK, 3, 2)], k=90)
        assert scores.questioned_level(skill)[0] <= scores.level_from_difficulty(8) - 1

    def test_strong_answer_after_level3_hint_does_not_raise_ceiling(self):
        skill = self._skill([(5, Band.STRONG, 0, 3), (8, Band.STRONG, 3, 4)])
        assert skill.ceiling == 5

    def test_core_misconception_caps_at_two(self):
        skill = self._skill([(7, Band.STRONG, 0, 4), (8, Band.STRONG, 0, 5)], k=95)
        skill.core_misconception = True
        assert scores.questioned_level(skill)[0] == 2

    def test_no_turns_no_level(self):
        assert scores.questioned_level(SkillState(key="x")) == (None, None)


class TestEvidenceStatus:
    """§2.6 evidence rules: never report a level without evidence."""

    def _skill(self, turns):
        skill = SkillState(key="x", k=50.0, c=50.0)
        for difficulty, band, weight in turns:
            scores.record_turn(skill, difficulty=difficulty, band=band, evaluation=make_evaluation(),
                               hint_level=0, weight=weight, core_misconception=False)
        return skill

    def test_zero_turns(self):
        assert scores.evidence_status(SkillState(key="x"), 3) == EvidenceStatus.NOT_ASSESSED

    def test_one_turn_is_insufficient(self):
        assert scores.evidence_status(self._skill([(4, Band.PARTIAL, 1.0)]), 3) == EvidenceStatus.INSUFFICIENT

    def test_one_strong_at_required_difficulty_is_enough(self):
        assert scores.evidence_status(self._skill([(5, Band.STRONG, 1.0)]), 3) == EvidenceStatus.ASSESSED
        assert scores.evidence_status(self._skill([(4, Band.STRONG, 1.0)]), 3) == EvidenceStatus.INSUFFICIENT

    def test_two_turns(self):
        assert scores.evidence_status(self._skill([(3, Band.WEAK, 1.0), (3, Band.PARTIAL, 1.0)]), 3) == EvidenceStatus.ASSESSED

    def test_revealed_attempts_are_not_evidence(self):
        assert scores.evidence_status(self._skill([(5, Band.STRONG, 0.0), (5, Band.STRONG, 0.0)]), 3) == EvidenceStatus.NOT_ASSESSED


class TestObserved:
    """§2.7"""

    @pytest.mark.parametrize("mean,level", [(0.29, 1), (0.30, 2), (0.44, 2), (0.45, 3), (0.59, 3), (0.60, 4), (0.77, 4), (0.78, 5)])
    def test_level_thresholds(self, mean, level):
        assert scores.observed_level(mean) == level

    def test_relevance_weighting_and_status(self):
        state = ObservedState(key="risk_awareness")
        scores.update_observed(state, make_evaluation(risk=0.8), Archetype.DESIGN)        # relevance 1.0
        scores.update_observed(state, make_evaluation(risk=0.2), Archetype.CONCEPTUAL)    # relevance 0.5
        assert state.weighted_sum / state.relevance_sum == pytest.approx((0.8 + 0.1) / 1.5)
        assert scores.observed_status(state) == EvidenceStatus.INSUFFICIENT
        for _ in range(4):
            scores.update_observed(state, make_evaluation(risk=0.7), Archetype.DEBUGGING)
        assert state.n_relevant == 5 and scores.observed_status(state) == EvidenceStatus.ASSESSED


class TestCalibration:
    """§2.10"""

    def test_labels(self):
        assert scores.calibration([(5, 0.5), (5, 0.4), (5, 0.6)])[1] == "overconfident"
        assert scores.calibration([(1, 0.9), (2, 0.8)])[1] == "underconfident"
        assert scores.calibration([(4, 0.75), (3, 0.6)])[1] == "well_calibrated"
        assert scores.calibration([]) == (None, None)


def test_company_modifiers_raise_the_emphasized_dimension():
    ev = make_evaluation(risk=0.5, clarity=0.5)
    out = scores.apply_company_modifiers(ev, {"risk_awareness": 0.30})
    assert out.risk_awareness > 0.5 > out.clarity
    assert scores.apply_company_modifiers(ev, None) == ev


def test_momentum():
    assert scores.momentum([Band.STRONG, Band.STRONG, Band.STRONG], 3) == 1.0
    assert scores.momentum([Band.STRONG, Band.WEAK, Band.WEAK, Band.PARTIAL], 3) == pytest.approx(-0.67)
    assert scores.momentum([], 3) == 0.0
