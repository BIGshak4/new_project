"""Typed objects the engine passes around.

Pydantic models so the live session state serializes straight into
`interview_session.state` (Data_Models §10) and the evaluator's JSON is validated
on the way in (AI_Engine_Spec §2.3).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

# ----------------------------------------------------------------------------- enums


class Band(StrEnum):
    STRONG = "STRONG"
    PARTIAL = "PARTIAL"
    WEAK = "WEAK"


class Action(StrEnum):
    ESCALATE = "ESCALATE"
    HOLD = "HOLD"
    HINT = "HINT"
    STEP_BACK = "STEP_BACK"
    PIVOT_TOPIC = "PIVOT_TOPIC"
    ENTER_SKILL = "ENTER_SKILL"
    END = "END"


class SkillStatus(StrEnum):
    UNTOUCHED = "untouched"
    ENTERING = "entering"
    HOLD_ZONE = "hold_zone"
    ESCALATING = "escalating"
    HINTING = "hinting"
    STRUGGLING = "struggling"
    STEPPING_BACK = "stepping_back"
    CEILING_FOUND = "ceiling_found"
    BASELINE_MAPPED = "baseline_mapped"


RESOLVED_STATUSES = {SkillStatus.CEILING_FOUND, SkillStatus.BASELINE_MAPPED}


class SubjectStatus(StrEnum):
    UNTOUCHED = "untouched"
    EXPLORING = "exploring"
    STRONG = "strong"
    MIXED = "mixed"
    WEAK = "weak"
    DONE = "done"


class Importance(StrEnum):
    CORE = "core"
    IMPORTANT = "important"
    NICE_TO_HAVE = "nice_to_have"


IMPORTANCE_RANK = {Importance.CORE: 3, Importance.IMPORTANT: 2, Importance.NICE_TO_HAVE: 1}


class AssessmentMode(StrEnum):
    QUESTIONED = "questioned"
    OBSERVED = "observed"


class SkillSource(StrEnum):
    ROLE = "role"
    COMPANY = "company"
    ROLE_AND_COMPANY = "role_and_company"
    USER_FOCUS = "user_focus"


class Archetype(StrEnum):
    CONCEPTUAL = "conceptual"
    CODING = "coding"
    DEBUGGING = "debugging"
    DESIGN = "design"
    BEHAVIORAL = "behavioral"


class EvidenceStatus(StrEnum):
    ASSESSED = "assessed"
    INSUFFICIENT = "insufficient_evidence"
    NOT_ASSESSED = "not_assessed"


class Bridge(StrEnum):
    STRENGTH_REFERENCE = "strength_reference"
    FRESH_START = "fresh_start"
    CLEAN_TOPIC = "clean_topic"
    LAST_AREA = "last_area"


# ----------------------------------------------------------------------------- evaluator


class Evaluation(BaseModel):
    """Exactly the JSON the Evaluator returns (AI_Engine_Spec §2.3)."""

    model_config = ConfigDict(extra="ignore")

    correctness: float = Field(ge=0, le=1)
    depth: float = Field(ge=0, le=1)
    clarity: float = Field(ge=0, le=1)
    structure: float = Field(ge=0, le=1)
    tradeoff_reasoning: float = Field(ge=0, le=1)
    risk_awareness: float = Field(ge=0, le=1)
    hedging_ratio: float = Field(ge=0, le=1)
    rubric_level_estimate: int = Field(ge=1, le=5)
    key_points_hit: list[str] = Field(default_factory=list)
    key_points_missed: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)
    behavior_signals: list[str] = Field(default_factory=list)
    one_line_summary: str = ""


class CheckResult(BaseModel):
    """Output of a deterministic check (Data_Models §13.4)."""

    type: str
    passed: bool | None            # None = the check could not run (unparseable answer, sim unavailable)
    detail: str = ""
    mismatches: list[dict] = Field(default_factory=list)
    runtime_ms: int = 0


# ----------------------------------------------------------------------------- catalog and plan


class CatalogSkill(BaseModel):
    key: str
    label: str
    subject: str | None = None                     # parent domain key; None for domain rows
    node_type: str = "skill"
    family: str = "hardware"
    category: str = "technical"
    default_assessment_mode: AssessmentMode | None = AssessmentMode.QUESTIONED
    min_difficulty: int = 1
    max_difficulty: int = 10
    prerequisites: list[str] = Field(default_factory=list)
    proficiency_rubric: dict[str, str] = Field(default_factory=dict)
    description: str = ""


class RoleSkillRow(BaseModel):
    skill: str
    weight: float
    importance: Importance
    required_level: dict[str, int]
    assessment_mode: AssessmentMode | None = None
    evaluation_notes: str | None = None


class CompanySkillRow(BaseModel):
    skill: str
    weight: float
    importance: Importance
    required_level_offset: int = 0
    required_level_min: int | None = None
    assessment_mode: AssessmentMode | None = None
    examination_notes: str | None = None
    scope: str = "all_roles"
    scope_family: str | None = None
    scope_role: str | None = None
    evidence: list[str] = Field(default_factory=list)      # ids of the company's dated evidence records (Data_Models §16)


class PlanSkill(BaseModel):
    """One row of the session skill plan (Data_Models §6.2)."""

    key: str
    subject: str
    source: SkillSource
    role_weight: float = 0.0
    company_weight: float = 0.0
    combined_weight: float
    importance: Importance
    required_level: int = Field(ge=1, le=5)
    assessment_mode: AssessmentMode
    planned_turns: int = 0
    priority_rank: int = 0
    min_difficulty: int = 1
    max_difficulty: int = 10
    prerequisites: list[str] = Field(default_factory=list)
    in_user_focus: bool = False
    examination_notes: str | None = None


# ----------------------------------------------------------------------------- live state


class TurnRecord(BaseModel):
    """What the engine remembers about one answer on a skill."""

    difficulty: int
    band: Band
    hint_level: int = 0
    rubric_level_estimate: int
    evidence_weight: float = 1.0
    core_misconception: bool = False
    archetype: Archetype = Archetype.CONCEPTUAL


class SkillState(BaseModel):
    key: str
    k: float | None = None
    c: float | None = None
    turns: int = 0
    ceiling: int | None = None                     # highest difficulty answered STRONG without a level-3 hint
    provisional_level: int | None = None
    status: SkillStatus = SkillStatus.UNTOUCHED
    budget: int = 2
    current_difficulty: int | None = None
    hint_level: int = 0                            # level of the hint currently in play
    partial_count: int = 0                         # PARTIAL answers at the current difficulty
    level3_hint_difficulty: int | None = None      # difficulty at which a level-3 hint was needed
    core_misconception: bool = False
    hints_used: int = 0
    history: list[TurnRecord] = Field(default_factory=list)
    resolved_reason: str | None = None

    @property
    def resolved(self) -> bool:
        return self.status in RESOLVED_STATUSES


class ObservedState(BaseModel):
    key: str
    weighted_sum: float = 0.0
    relevance_sum: float = 0.0
    n: int = 0
    n_relevant: int = 0                            # turns with relevance 1.0
    provisional_level: int | None = None


class SubjectState(BaseModel):
    key: str
    weight: float = 0.0
    importance: Importance = Importance.NICE_TO_HAVE
    required_level: float = 1.0
    k: float | None = None
    c: float | None = None
    level: float | None = None
    status: SubjectStatus = SubjectStatus.UNTOUCHED
    momentum: float = 0.0
    turns_used: int = 0
    turns_planned: int = 0
    turns_planned_original: int = 0
    skills_planned: int = 0
    skills_resolved: int = 0
    weak_answers: int = 0
    recent_bands: list[Band] = Field(default_factory=list)
    closed_early: bool = False
    left_at_turn: int | None = None
    final_momentum: float | None = None            # momentum when the subject was last left
    rebalanced_for: SubjectStatus | None = None    # status the turn allocation was last adjusted for

    @property
    def coverage(self) -> float:
        return self.skills_resolved / self.skills_planned if self.skills_planned else 1.0


class Decision(BaseModel):
    """The authoritative instruction to the Question Generator (Data_Models §11)."""

    action: Action
    reason_code: str
    target_subject: str | None = None
    target_skill: str | None = None
    target_difficulty: int | None = None
    target_archetype: Archetype = Archetype.CONCEPTUAL
    subject_switch: bool = False
    entry_difficulty_reason: dict[str, int] | None = None
    bridge: Bridge | None = None
    bridge_from_skill: str | None = None
    probe_focus: str | None = None
    invite_observed_skills: list[str] = Field(default_factory=list)
    deliver_hint: bool = False
    hint_level: int = 0
    deliver_tip: bool = False
    rebalance_codes: list[str] = Field(default_factory=list)


class SessionState(BaseModel):
    """Live session state, stored in interview_session.state in the MVP (Data_Models §10)."""

    version: int = 0
    turn_index: int = 0
    seniority: str = "junior"
    baseline_difficulty: int = 2
    difficulty_ceiling: int = 6
    planned_duration_min: float = 45.0
    elapsed_ms: int = 0
    current_skill: str | None = None
    current_subject: str | None = None
    current_difficulty: int | None = None
    skill_state: dict[str, SkillState] = Field(default_factory=dict)
    observed_state: dict[str, ObservedState] = Field(default_factory=dict)
    subject_state: dict[str, SubjectState] = Field(default_factory=dict)
    subjects_visited_order: list[str] = Field(default_factory=list)
    skill_turns_planned: dict[str, int] = Field(default_factory=dict)   # live allocation after rebalancing
    recent_bands: list[Band] = Field(default_factory=list)
    recent_actions: list[Action] = Field(default_factory=list)
    turn_pool_released: int = 0
    tip_last_delivered_turn: dict[str, int] = Field(default_factory=dict)
    history_summary: str = ""

    @property
    def remaining_min(self) -> float:
        return max(0.0, self.planned_duration_min - self.elapsed_ms / 60_000)
