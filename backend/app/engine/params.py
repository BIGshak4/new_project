"""Every tunable number in the engine, in one place.

Defaults come from AI_Engine_Spec.md. Change a value here, run the tests and the
replay simulator, and nothing else needs to move. Where the spec leaves a value
open, the choice is marked ASSUMPTION so it is easy to find and revisit.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScoreParams:
    # §2.4 score update
    a_k: float = 0.45
    a_k_first_turns: float = 0.60          # first two turns on a skill replace the prior quickly
    first_turns_count: int = 2
    a_c: float = 0.35
    hint_penalty_per_level: float = 8.0
    difficulty_factor_base: float = 0.6
    difficulty_factor_span: float = 0.4
    knowledge_correctness_weight: float = 0.65
    knowledge_depth_weight: float = 0.35
    conf_clarity_weight: float = 0.35
    conf_hedging_weight: float = 0.25
    conf_latency_weight: float = 0.20
    conf_revision_weight: float = 0.20
    # ASSUMPTION: the spec names latency_norm and revision_norm without defining them.
    # An answer within the expected time scores 1.0, three times over scores 0.0.
    expected_answer_ms_base: int = 30_000
    expected_answer_ms_per_difficulty: int = 15_000
    latency_slow_ratio: float = 3.0
    revision_cap: int = 5

    # §3.1 answer bands
    strong_correctness: float = 0.75
    strong_depth: float = 0.55
    partial_correctness: float = 0.45

    # §2.3 deterministic check authority
    check_fail_correctness_cap: float = 0.40
    check_pass_correctness_floor: float = 0.60

    # §2.5 priors
    seniority_prior_k: dict[str, float] = field(default_factory=lambda: {
        "student": 32.0,                   # ASSUMPTION: spec lists junior and above only
        "junior": 40.0, "mid": 55.0, "senior": 65.0, "staff": 72.0, "principal": 78.0,
    })
    prior_c_default: float = 50.0          # ASSUMPTION: neutral starting confidence
    prior_decay_per_30_days: float = 0.10
    prior_prerequisite_offset: float = -10.0
    prior_subject_offset: float = -5.0
    calibration_prior_adjust: float = 5.0

    # §2.6 level from scores
    level_ceiling_weight: float = 0.50
    level_rubric_weight: float = 0.35
    level_k_weight: float = 0.15
    core_misconception_level_cap: int = 2

    # §2.7 observed skills
    observed_level_thresholds: tuple[float, float, float, float] = (0.30, 0.45, 0.60, 0.78)
    observed_relevance_default: float = 0.5
    observed_min_relevant_turns: int = 5

    # §2.10 calibration
    calibration_band: float = 0.25


@dataclass(frozen=True)
class EvidenceParams:
    """§2.9 evidence weight = base(mode) x familiarity x assistance x exposure x reveal."""

    base: dict[str, float] = field(default_factory=lambda: {
        "quick": 0.3, "deep": 1.0, "simulation": 1.0, "diagnostic": 0.5, "retention_check": 1.2,
    })
    familiarity: dict[str, float] = field(default_factory=lambda: {
        "new": 1.0, "seen_variation": 0.7, "seen_same": 0.4,
    })
    assistance: dict[int, float] = field(default_factory=lambda: {0: 1.0, 1: 0.8, 2: 0.6, 3: 0.4})
    exposure: dict[str, float] = field(default_factory=lambda: {"low": 1.0, "medium": 0.85, "high": 0.6})


@dataclass(frozen=True)
class ControllerParams:
    """§3 skill controller."""

    struggle_budget_per_skill: int = 2
    double_escalate_confidence: float = 80.0
    double_escalate_depth: float = 0.80
    soft_ceiling_confidence: float = 60.0
    step_back_delta: int = 2
    max_hint_level: int = 3


@dataclass(frozen=True)
class RouterParams:
    """§4 subject router."""

    w_weight: float = 1.0
    w_uncover: float = 0.8
    w_core_gap: float = 0.9
    w_stay: float = 0.5
    w_focus: float = 0.6
    w_strong: float = 0.6
    w_fatigue: float = 0.9
    w_recent: float = 0.5
    fatigue_momentum: float = -0.5
    recent_turns_window: int = 2
    # §4.4 skill priority
    skill_core_bonus: float = 0.5
    skill_focus_bonus: float = 0.4
    skill_prereq_resolved_bonus: float = 0.3
    skill_prereq_unresolved_penalty: float = 0.6
    # §4.5 entry difficulty
    entry_strong_adjust: int = 2
    entry_high_k_adjust: int = 1
    entry_high_k_threshold: float = 70.0
    entry_mixed_low_adjust: int = -1
    entry_mixed_low_threshold: float = 55.0
    entry_weak_adjust: int = -2
    entry_momentum_threshold: float = 0.75
    entry_max_above_baseline: int = 3
    entry_max_below_baseline: int = 2
    session_momentum_window: int = 4
    subject_momentum_window: int = 3
    # §4.2 status thresholds
    strong_level_margin: float = 0.5
    weak_level_margin: float = 1.0
    # §4.6 rebalancing
    strong_turn_factor: float = 0.6
    weak_cap_factor: float = 1.5
    # §4.3 / §4.9 time overrides
    ending_override_minutes: float = 6.0
    end_session_minutes: float = 4.0
    minutes_per_turn: float = 1.8
    # §4.7 observed coverage
    observed_core_min_relevant_turns: int = 3


@dataclass(frozen=True)
class PlanRouterParams:
    """§4.11 plan router."""

    w_gap: float = 1.0
    w_unassessed_early: float = 0.8
    w_unassessed_late: float = 0.3
    coverage_switch: float = 0.70
    w_retention: float = 0.7
    w_core: float = 0.6
    w_variety: float = 0.3
    w_fatigue: float = 0.8
    w_time: float = 1.0
    retention_first_days: tuple[int, int] = (3, 5)
    retention_next_days: tuple[int, int] = (10, 14)
    final_days_reserved: int = 5
    diagnostic_items: tuple[int, int] = (8, 12)
    estimated_minutes: dict[str, int] = field(default_factory=lambda: {
        "quick": 4, "deep": 20, "simulation": 40, "diagnostic": 15, "retention_check": 12,
    })


@dataclass(frozen=True)
class ScorecardParams:
    """Data_Models §7.2 and §7.3."""

    core_gap_two_levels_cap: float = 60.0
    core_gap_one_level_cap: float = 80.0
    partial_evaluation_coverage: float = 0.6
    rollup_recency_decay: float = 0.7
    trend_threshold: float = 0.5


@dataclass(frozen=True)
class EngineParams:
    scores: ScoreParams = field(default_factory=ScoreParams)
    evidence: EvidenceParams = field(default_factory=EvidenceParams)
    controller: ControllerParams = field(default_factory=ControllerParams)
    router: RouterParams = field(default_factory=RouterParams)
    plan_router: PlanRouterParams = field(default_factory=PlanRouterParams)
    scorecards: ScorecardParams = field(default_factory=ScorecardParams)


DEFAULT_PARAMS = EngineParams()
