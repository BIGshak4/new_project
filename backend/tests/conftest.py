"""Shared fixtures: the Design Verification example used throughout the specs."""

from __future__ import annotations

import pytest

from app.schemas.engine import (
    AssessmentMode,
    CatalogSkill,
    CompanySkillRow,
    Evaluation,
    Importance,
    RoleSkillRow,
)

LEVELS = {"junior": 2, "mid": 3, "senior": 4, "staff": 4, "principal": 5}


def _skill(key, subject, *, mode=AssessmentMode.QUESTIONED, lo=1, hi=10, prereq=()):
    return CatalogSkill(key=key, label=key, subject=subject, default_assessment_mode=mode,
                        min_difficulty=lo, max_difficulty=hi, prerequisites=list(prereq))


@pytest.fixture
def catalog() -> dict[str, CatalogSkill]:
    skills = [
        _skill("sv_assertions", "systemverilog", lo=4, hi=9),
        _skill("sv_randomization", "systemverilog"),
        _skill("uvm_sequences", "uvm"),
        _skill("uvm_scoreboard_monitor", "uvm"),
        _skill("fsm_coverage", "uvm"),
        _skill("fifo_verification", "hw_queues", lo=2, hi=8),
        _skill("ooo_scoreboard", "hw_queues", lo=5, hi=10, prereq=["fifo_verification"]),
        _skill("debugging_methodology", "debugging", lo=3, hi=10),
        _skill("formal_verification", "verification_methods"),
        _skill("ownership", "values"),
        _skill("structured_communication", "communication", mode=AssessmentMode.OBSERVED),
        _skill("tradeoff_reasoning", "engineering_judgment", mode=AssessmentMode.OBSERVED),
        _skill("risk_awareness", "engineering_judgment", mode=AssessmentMode.OBSERVED),
    ]
    return {s.key: s for s in skills}


@pytest.fixture
def dv_role_rows() -> list[RoleSkillRow]:
    """Data_Models §4.2 example: Design Verification Engineer. Weights sum to 1.0."""
    def row(skill, weight, importance, levels=None, mode=None):
        return RoleSkillRow(skill=skill, weight=weight, importance=importance,
                            required_level=levels or LEVELS, assessment_mode=mode)
    return [
        row("sv_assertions", 0.14, Importance.CORE),
        row("uvm_sequences", 0.14, Importance.CORE),
        row("uvm_scoreboard_monitor", 0.12, Importance.CORE),
        row("ooo_scoreboard", 0.10, Importance.IMPORTANT, {"junior": 1, "mid": 2, "senior": 3, "staff": 4, "principal": 5}),
        row("fsm_coverage", 0.10, Importance.IMPORTANT, {"junior": 2, "mid": 3, "senior": 3, "staff": 4, "principal": 5}),
        row("sv_randomization", 0.10, Importance.IMPORTANT),
        row("fifo_verification", 0.08, Importance.IMPORTANT, {"junior": 2, "mid": 3, "senior": 3, "staff": 4, "principal": 4}),
        row("debugging_methodology", 0.10, Importance.CORE),
        row("structured_communication", 0.06, Importance.IMPORTANT, {"junior": 2, "mid": 3, "senior": 3, "staff": 4, "principal": 4}, AssessmentMode.OBSERVED),
        row("tradeoff_reasoning", 0.06, Importance.NICE_TO_HAVE, {"junior": 1, "mid": 2, "senior": 3, "staff": 4, "principal": 5}, AssessmentMode.OBSERVED),
    ]


@pytest.fixture
def semi_company_rows() -> list[CompanySkillRow]:
    """Data_Models §5.2 example: Example Semiconductor Co., as it applies to the DV role."""
    return [
        CompanySkillRow(skill="risk_awareness", weight=0.30, importance=Importance.CORE,
                        required_level_offset=1, assessment_mode=AssessmentMode.OBSERVED),
        CompanySkillRow(skill="ownership", weight=0.15, importance=Importance.IMPORTANT, required_level_min=3),
        CompanySkillRow(skill="debugging_methodology", weight=0.25, importance=Importance.CORE,
                        required_level_offset=1, scope="family", scope_family="hardware"),
        CompanySkillRow(skill="formal_verification", weight=0.20, importance=Importance.IMPORTANT,
                        required_level_min=3, scope="role", scope_role="design-verification-engineer"),
        CompanySkillRow(skill="sv_assertions", weight=0.10, importance=Importance.IMPORTANT,
                        scope="role", scope_role="design-verification-engineer"),
    ]


def make_evaluation(correctness=0.8, depth=0.6, clarity=0.7, structure=0.6, tradeoff=0.5, risk=0.5,
                    hedging=0.2, level=3, **extra) -> Evaluation:
    return Evaluation(correctness=correctness, depth=depth, clarity=clarity, structure=structure,
                      tradeoff_reasoning=tradeoff, risk_awareness=risk, hedging_ratio=hedging,
                      rubric_level_estimate=level, **extra)
