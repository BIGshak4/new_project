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
    focus: str | None = None                    # what was hard in this attempt (a bank misconception's explanation)


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
    xp_earned: int | None = None                # XP this scored answer earned (app.engine.xp); None until it is scored


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


class LabelledSkill(BaseModel):
    key: str
    label: str


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
    loyalty: int | None = None                  # 1..10: how fresh the evidence behind the level is (None: never assessed)
    needs_refresh: bool = False                 # loyalty in the provisional band: re-check before trusting the level
    xp: int = 0                                 # XP earned on this skill (split of each answer's XP by the question's skill weights)
    level_progress: float = 0.0                 # 0..1 fill toward the next level, from the engine's own level score (xp.level_progress)


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


class GoalView(BaseModel):
    """What the user is preparing for. Asked once at the start; editable any time."""

    job_type: str | None = None                 # a key from GET /v1/job-types
    job_type_label: str | None = None
    interview_date: str | None = None           # ISO date
    days_to_interview: int | None = None        # negative once the date has passed
    minutes_per_day: int | None = None
    seniority: str | None = None                # student | junior | mid | senior | staff | principal
    complete: bool = False                      # job type and minutes are known: the onboarding was answered


class JobTypeView(BaseModel):
    key: str
    label: str
    description: str


class CompanyView(BaseModel):
    slug: str
    name: str
    questions: int                              # distinct questions reported at this company
    sightings: int                              # reports in total


class ProgressOverview(BaseModel):
    """The one card that should make the user feel the distance covered: counts and a level in words, no percentages."""

    answered: int                               # scored answers so far
    strong: int
    partial: int
    weak: int
    skills_assessed: int                        # assessed AND fresh enough to trust
    skills_to_refresh: int = 0                  # assessed once, but the evidence is old: a refresh is scheduled
    skills_total: int                           # skills in the plan for this user's goal
    level: str                                  # a word: Getting started | Awareness | Foundational | Proficient | Advanced | Expert
    level_rank: int                             # 0..5, for the meter
    message: str                                # one encouraging sentence in the practice language
    xp_total: int = 0                           # XP over every scored answer and interview turn (computed on read)
    xp_today: int = 0                           # ... of which today (UTC)
    streak_days: int = 0                        # consecutive UTC days with a scored answer, ending today or yesterday


class TimelinePoint(BaseModel):
    day: str                                    # ISO date
    answered: int
    strong: int
    partial: int
    weak: int
    level: float | None = None                  # average assessed level across skills at the end of that day


class PlanItemView(BaseModel):
    id: str | None = None                       # the saved plan item (start it with POST /v1/me/program/start)
    day_index: int                              # 0 = today; an open item from an earlier day shows as today (carried)
    date: str                                   # ISO date of the day it is shown on
    mode: str                                   # quick | deep | simulation | diagnostic | retention_check
    skills: list[LabelledSkill] = Field(default_factory=list)
    minutes: int
    reason: str
    done: bool = False                          # status done: an attempt or interview fulfilled it
    status: str = "planned"                     # planned | started | done | skipped
    carried: bool = False                       # planned for an earlier day and not done yet: carried forward


class PlanView(BaseModel):
    items: list[PlanItemView] = Field(default_factory=list)
    minutes_per_day: int
    days_to_interview: int | None = None
    interview_date: str | None = None
    generated_for: str                          # ISO date the plan week starts on
    saved: bool = False                         # persisted: skipped days are carried forward, finished items stay ticked


class ProgramView(BaseModel):
    """The saved program as it stands today: what is due now and what comes next."""

    plan: PlanView
    today: list[PlanItemView] = Field(default_factory=list)      # open items due today, carried-forward ones first
    next: PlanItemView | None = None                             # the one to start now
    done_today: int = 0
    minutes_due_today: int = 0
    goal_complete: bool = False


class ProgramStartView(BaseModel):
    kind: str                                   # attempt | interview | nothing
    item: PlanItemView | None = None
    attempt: AttemptView | None = None          # kind attempt: the attempt that was opened for the item
    interview_duration_min: int | None = None   # kind interview: the duration to offer in the lobby
    message: str | None = None                  # kind nothing: why (no goal, nothing due, no question in the bank)


class ProgressView(BaseModel):
    skills: list[SkillProgress]
    subjects: list[SubjectProgress] = Field(default_factory=list)
    recent: list[dict]
    attempts_today: int
    daily_limit: int
    overview: ProgressOverview | None = None
    timeline: list[TimelinePoint] = Field(default_factory=list)
    plan: PlanView | None = None
    goal: GoalView | None = None


# ----------------------------------------------------------------------------- mock interviews


class InterviewPlanSkill(BaseModel):
    skill: str
    label: str
    subject: str
    importance: str                             # core | important | nice_to_have
    required_level: int
    planned_turns: int


class InterviewTurnView(BaseModel):
    """One interviewer question. Results stay hidden until the interview is over, like a real interview."""

    index: int
    skill: str
    skill_label: str
    subject: str
    difficulty: int
    archetype: str
    question: str
    question_key: str | None = None
    trial: bool = False                         # the question is "on trial" (checked live before publication)
    status: str                                 # open | evaluating | done | failed
    hints: list[HintView] = Field(default_factory=list)
    answer: str | None = None
    visual: VisualAnswer | None = None          # a drawn circuit and/or photos sent with the answer
    flags: list[str] = Field(default_factory=list)   # circuit_assessed | images_assessed | images_unavailable | ...
    asked_at: str
    answered_at: str | None = None
    # revealed only when the session is completed
    band: str | None = None
    summary: str | None = None
    key_points_hit: list[str] = Field(default_factory=list)
    key_points_missed: list[str] = Field(default_factory=list)
    check: CheckView | None = None
    action_after: str | None = None             # what the interviewer decided next: ESCALATE, HOLD, HINT, STEP_BACK, ENTER_SKILL, END
    subject_switch: bool = False
    xp_earned: int | None = None                # XP for this turn, revealed with the results (interview turns count x1.5)


class InterviewView(BaseModel):
    id: str
    status: str                                 # in_progress | evaluating | completed
    language: str
    duration_min: int
    elapsed_ms: int
    remaining_min: float
    started_at: str
    ended_at: str | None = None
    ended_early: bool = False
    turn_count: int
    current_turn: InterviewTurnView | None      # the question waiting for an answer
    turns: list[InterviewTurnView]              # answered questions, oldest first
    plan: list[InterviewPlanSkill]
    can_answer: bool
    can_hint: bool
    hints_used: int
    results_revealed: bool                      # bands and summaries are shown once the interview is over
    report_ready: bool


class InterviewListItem(BaseModel):
    id: str
    status: str
    duration_min: int | None = None
    language: str | None = None
    turn_count: int
    started_at: str | None = None
    ended_at: str | None = None


class FitView(BaseModel):
    fit_score: float | None
    skills_total: int
    skills_assessed: int
    skills_meeting_requirement: int
    core_gaps: list[str] = Field(default_factory=list)
    top_strengths: list[str] = Field(default_factory=list)
    domain_breakdown: dict[str, float] = Field(default_factory=dict)
    partial_evaluation: bool = False
    cap_applied: float | None = None


class SkillReportView(BaseModel):
    key: str
    label: str
    subject: str
    status: str                                 # assessed | insufficient_evidence | not_assessed
    proficiency_level: int | None
    required_level: int
    level_gap: int | None
    turns_count: int
    hints_used: int
    importance: str
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class InterviewReportView(BaseModel):
    session_id: str
    language: str
    duration_min: int
    turn_count: int
    fit: dict[str, FitView]                     # role | company | session_overall
    skills: list[SkillReportView]
    subjects: list[dict]
    timeline: list[dict]
    recommended_next_skills: list[LabelledSkill]
    cover_next_time: list[LabelledSkill]
    top_tips: list[str]
    narrative_md: str
    narrative_source: str                       # generated | fallback
    turns: list[InterviewTurnView]
