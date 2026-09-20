"""What the web app receives. Safe by construction: no reference solutions, no raw scores,
no hidden hints, no expected answers of follow-ups."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.repo.questions import QuestionDetail
from app.schemas.visual_answer import VisualAnswer


class HintView(BaseModel):
    level: int
    text: str


class CheckView(BaseModel):
    type: str                                   # truth_table | numeric | code_tests
    passed: bool | None
    detail: str
    mismatches: list[dict] = Field(default_factory=list)   # the first differing rows / test cases


class CardView(BaseModel):
    what_happened: str
    why_it_matters: str
    next_step: str
    your_reasoning_vs_reference: str


class TipView(BaseModel):
    key: str
    text: str


class NextQuestionView(BaseModel):
    key: str
    title: str
    subject: str
    skill: str
    difficulty: int
    why: str                                    # reinforce | consolidate | advance | explore
    reason: str                                 # one sentence in the practice language


class SubmissionView(BaseModel):
    revision: int
    key: str
    turn: int                                   # 0 = main question, n = n-th follow-up
    answer: str
    visual: VisualAnswer | None = None
    status: str                                 # evaluating | done | failed
    accepted_at: str
    evaluated_at: str | None = None
    band: str | None = None
    summary: str | None = None                  # the evaluator's one-line summary
    key_points_hit: list[str] = Field(default_factory=list)
    key_points_missed: list[str] = Field(default_factory=list)
    check: CheckView | None = None
    card: CardView | None = None
    tip: TipView | None = None
    follow_up: str | None = None                # the next question this answer produced, if any
    assessed_by: str = "demo"                  # demo | model: whether a real model judged this answer
    model: str | None = None                    # the model id when assessed_by == model
    hints_seen: int = 0                         # immutable assistance snapshot when this answer was accepted
    reference_seen: bool = False
    evidence: str = "none"                      # full | reduced | none: whether and how much this counted
    flags: list[str] = Field(default_factory=list)
    replayed: bool = False
    next_question: NextQuestionView | None = None   # what to practise next, decided from this evaluation


class FollowUpView(BaseModel):
    turn: int
    question: str
    action: str
    created_at: str
    submission: SubmissionView | None = None


class AttemptView(BaseModel):
    id: str
    question: QuestionDetail
    mode: str
    language: str
    self_confidence_before: int | None
    status: str                                 # in_progress | evaluating | done | failed
    started_at: str
    hints: list[HintView]                       # hints already shown, in order
    hints_remaining: int
    reference: str | None                       # only after reveal
    submission: SubmissionView | None           # the main answer
    follow_ups: list[FollowUpView]
    pending_follow_up: FollowUpView | None
    can_submit: bool
    can_retry: bool
    next_question: NextQuestionView | None = None   # the latest suggestion, kept across refreshes


class SkillProgress(BaseModel):
    key: str
    label: str
    subject: str
    level: int | None
    status: str                                 # not_assessed | insufficient | assessed
    trend: str
    required_level: int
    assessments: int
    last_assessed_at: str | None
    retention_due_at: str | None


class SubjectProgress(BaseModel):
    """One subject (topic) as a whole: what the donut charts draw."""

    key: str
    label: str
    skills_total: int                           # skills of this subject in the role plan
    skills_assessed: int                        # with enough evidence for a level
    skills_started: int                         # with at least one answer
    levels: dict[str, int]                      # level -> number of skills at that level ("1".. "5")
    average_level: float | None
    bands: dict[str, int]                       # STRONG / PARTIAL / WEAK answer counts in this subject
    attempts: int
    weight: float                               # share of the role plan (0-1)
    questions_available: int


class ProgressView(BaseModel):
    skills: list[SkillProgress]
    subjects: list[SubjectProgress] = Field(default_factory=list)
    recent: list[dict]
    attempts_today: int
    daily_limit: int
