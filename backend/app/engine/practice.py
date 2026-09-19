"""Deep and quick practice: one question, end to end (AI_Engine_Spec §1.1, §6.6).

    hints (bank, levels 1-3) -> submit -> deterministic check -> evaluator -> band ->
    evidence weight -> scores per examined skill -> feedback card + at most one tip ->
    skill controller -> optional follow-up (probe, scaffold, step back, one escalation)

Built for the real world, not the happy path:

* An answer is ACCEPTED first and EVALUATED second. Acceptance creates an immutable
  `Submission` (a revision) with an idempotency key; evaluation has its own state
  (pending / evaluating / done / failed). A failed evaluation keeps the answer and can
  be retried without a second score update.
* Replaying a submission with the same key returns the existing result. The same key
  with a different answer is a conflict. Scores are applied exactly once per revision.
* Every hint and reveal is an `ExposureEvent`. Evidence for a revision is computed
  from what had been exposed when that revision was accepted, so an answer written
  after the reference was shown earns nothing, while an earlier answer retried after
  a failure keeps its evidence.
* What the candidate was shown (check, card, tip, follow-up) is stored on the revision,
  so after a refresh or a server restart `restore()` rebuilds the attempt from
  `attempt_row()` and shows the same thing again, without scoring anything twice.

Everything the caller must persist comes back in the outcome and in `attempt_row()`.
"""

from __future__ import annotations

import asyncio
import dataclasses
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.engine import ENGINE_VERSION, checks, evaluator, feedback, generator, scores, skill_controller, tips
from app.engine.evaluator import EvaluationResult
from app.engine.feedback import FeedbackCard
from app.engine.params import DEFAULT_PARAMS, EngineParams
from app.engine.providers import LLMUsage, Provider
from app.schemas.bank import BankQuestion, Tip
from app.schemas.engine import (
    Action,
    AssessmentMode,
    Band,
    CatalogSkill,
    CheckResult,
    Decision,
    Evaluation,
    Importance,
    PlanSkill,
    SkillSource,
    SkillState,
)

MAX_FOLLOW_UPS = 2
MAX_ANSWER_CHARS = 20_000
DEMO_MODELS = {"demo", "scripted", "manual", ""}


def assessed_by(model: str | None) -> str:
    """'model' when a real model judged the answer, 'demo' for the scripted/manual stand-ins."""
    return "demo" if (model or "") in DEMO_MODELS else "model"
# a revision still pending/evaluating after this long was interrupted (crash, lost worker) and may be retried;
# younger ones are being evaluated right now, possibly by another process
EVALUATION_BUDGET_SECONDS = 600


class PracticeError(Exception):
    """A client error: the request cannot be honored as sent. Carries a stable code for the API."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class EvaluationStatus(StrEnum):
    PENDING = "pending"
    EVALUATING = "evaluating"
    DONE = "done"
    FAILED = "failed"


class ExposureEvent(BaseModel):
    sequence: int
    kind: str                                   # hint | reference
    level: int = 0                              # hint level, 0 for reference
    at: str


class Submission(BaseModel):
    """One accepted answer revision. Immutable once accepted; only its evaluation state changes."""

    revision: int
    key: str                                    # idempotency key from the client, or generated
    turn: int                                   # 0 = the main question, n = the n-th follow-up
    answer: str
    hints_seen: int                             # exposure snapshot at acceptance
    reference_seen: bool
    exposure_sequence: int
    status: EvaluationStatus = EvaluationStatus.PENDING
    attempts: int = 0
    accepted_at: str
    evaluating_since: str | None = None        # set when an evaluation starts; cleared when it ends
    evaluated_at: str | None = None
    band: Band | None = None
    evaluation: dict | None = None
    flags: list[str] = Field(default_factory=list)
    # what the candidate was shown for this revision, so a refresh or a restart can show it again
    check: dict | None = None
    evidence_weight: float = 0.0
    card: dict | None = None
    tip_key: str | None = None
    tip_text: str | None = None
    follow_up: str | None = None
    evaluator_model: str | None = None         # which model judged this revision ("demo" for the scripted stand-in)


@dataclass
class PracticeContext:
    provider: Provider
    skills: dict[str, CatalogSkill]
    language: str = "en"
    seniority: str = "student"
    difficulty_ceiling: int = 5
    required_levels: dict[str, int] = field(default_factory=dict)
    skill_weights: dict[str, float] = field(default_factory=dict)
    tips: list[Tip] = field(default_factory=list)
    glossary: list[dict] = field(default_factory=list)
    role_family: str | None = "hardware"
    polish_tips: bool = True
    params: EngineParams = DEFAULT_PARAMS


@dataclass
class UsageEvent:
    action: str
    model: str
    usage: LLMUsage
    latency_ms: int

    def as_row(self, mode: str) -> dict:
        cost = self.usage.cost_usd(self.model)
        return {"mode": mode, "action": self.action, "model": self.model, "tokens_in": self.usage.input_tokens,
                "tokens_out": self.usage.output_tokens, "cache_read_tokens": self.usage.cache_read_tokens,
                "cache_write_tokens": self.usage.cache_write_tokens,
                "cost_usd": cost if cost is not None else 0.0, "latency_ms": self.latency_ms,
                "meta": {"price_known": cost is not None}}


@dataclass
class PracticeOutcome:
    submission: Submission
    band: Band | None
    evaluation: Evaluation | None
    check: CheckResult | None
    evidence_weight: float
    card: FeedbackCard | None
    tip_text: str | None
    tip_key: str | None
    follow_up: str | None                       # the next question to show, or None when the attempt is complete
    decision: Decision | None
    metrics: list[dict] = field(default_factory=list)
    usage: list[UsageEvent] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    replayed: bool = False                      # True when an idempotent replay returned the stored result

    @property
    def status(self) -> EvaluationStatus:
        return self.submission.status


def _now() -> str:
    return datetime.now(UTC).isoformat()


class PracticeAttempt:
    def __init__(self, ctx: PracticeContext, question: BankQuestion, skill_states: dict[str, SkillState], *,
                 mode: str = "deep", evidence_mode: str | None = None, familiarity: str = "new",
                 self_confidence: int | None = None, attempt_id: str | None = None):
        self._init_common(ctx, question, skill_states, mode=mode, evidence_mode=evidence_mode, familiarity=familiarity,
                          self_confidence=self_confidence, attempt_id=attempt_id)
        state = self._state(question.primary_skill)
        skill_controller.enter_skill(state, question.difficulty, ctx.params)
        # the profile's state is long-lived; every attempt starts with a fresh struggle budget
        state.budget = ctx.params.controller.struggle_budget_per_skill

    def _init_common(self, ctx: PracticeContext, question: BankQuestion, skill_states: dict[str, SkillState], *,
                     mode: str, evidence_mode: str | None, familiarity: str, self_confidence: int | None,
                     attempt_id: str | None) -> None:
        if self_confidence is not None and not 1 <= self_confidence <= 5:
            raise PracticeError("validation", "self_confidence must be between 1 and 5")
        self.ctx, self.question = ctx, question
        self.attempt_id = attempt_id or str(uuid.uuid4())
        self.skill_states = skill_states
        self.mode = mode                                   # attempt.mode: quick | deep
        self.evidence_mode = evidence_mode or mode         # also diagnostic | retention_check (AI_Engine_Spec §2.9)
        self.familiarity = familiarity
        self.self_confidence = self_confidence
        self.language_fallback = ctx.language not in question.translations

        self.exposures: list[ExposureEvent] = []
        self.submissions: list[Submission] = []
        self.follow_up_turns: list[dict] = []              # [{turn, question, generated, action, difficulty, expected_answer_outline, submission_revision?}]
        self.misconceptions_hit: list[str] = []
        self._outcomes: dict[int, PracticeOutcome] = {}    # revision -> outcome, for idempotent replay
        self._lock = asyncio.Lock()
        self._escalated = False
        self._tip_turns: dict[str, int] = {}
        self._follow_up_difficulty = question.difficulty

        primary = question.primary_skill
        catalog_skill = ctx.skills[primary]
        self.plan_skill = PlanSkill(
            key=primary, subject=catalog_skill.subject or question.subject, source=SkillSource.ROLE,
            combined_weight=ctx.skill_weights.get(primary, 0.1), importance=Importance.IMPORTANT,
            required_level=ctx.required_levels.get(primary, 2), assessment_mode=AssessmentMode.QUESTIONED,
            min_difficulty=catalog_skill.min_difficulty, max_difficulty=catalog_skill.max_difficulty,
            prerequisites=list(catalog_skill.prerequisites))

    @classmethod
    def restore(cls, ctx: PracticeContext, question: BankQuestion, skill_states: dict[str, SkillState],
                row: dict) -> PracticeAttempt:
        """Rebuild an attempt from `attempt_row()` after a refresh or a restart.

        Nothing is re-scored: `skill_states` is the profile as already updated, so the skill is not
        entered again and the struggle budget is not reset. A submission that was caught mid-evaluation
        by the restart becomes FAILED, so `retry_evaluation()` can finish it with the saved answer.
        """
        self = cls.__new__(cls)
        self._init_common(ctx, question, skill_states, mode=row["mode"], evidence_mode=row.get("evidence_mode"),
                          familiarity=row.get("familiarity") or "new", self_confidence=row.get("self_confidence_before"),
                          attempt_id=row["id"])
        self.exposures = [ExposureEvent.model_validate(e) for e in row.get("exposures") or []]
        self.submissions = [Submission.model_validate(s) for s in row.get("submissions") or []]
        self.follow_up_turns = [dict(t) for t in row.get("follow_up_turns") or []]
        self.misconceptions_hit = list(row.get("misconceptions_hit") or [])
        self._tip_turns = {k: int(v) for k, v in (row.get("tip_turns") or {}).items()}
        self._escalated = any(t.get("action") == Action.ESCALATE.value for t in self.follow_up_turns)
        if self.follow_up_turns:
            self._follow_up_difficulty = self.follow_up_turns[-1].get("difficulty") or question.difficulty
        for submission in self.submissions:
            if submission.status in (EvaluationStatus.PENDING, EvaluationStatus.EVALUATING) and self._interrupted(submission):
                submission.status = EvaluationStatus.FAILED
                submission.evaluating_since = None
                submission.flags = [*submission.flags, "evaluation_interrupted"]
            self._outcomes[submission.revision] = self._outcome_from(submission)
        return self

    @staticmethod
    def _interrupted(submission: Submission, *, now: datetime | None = None) -> bool:
        """A pending revision older than the evaluation budget was abandoned; a younger one is in flight."""
        started = submission.evaluating_since or submission.accepted_at
        age = (now or datetime.now(UTC)) - datetime.fromisoformat(started)
        return age.total_seconds() > EVALUATION_BUDGET_SECONDS

    @staticmethod
    def _outcome_from(submission: Submission) -> PracticeOutcome:
        """The stored result of a revision, as the outcome a replay returns. Usage is not repeated: it was metered once."""
        check = CheckResult.model_validate(submission.check) if submission.check else None
        if submission.status != EvaluationStatus.DONE:
            return PracticeOutcome(submission, None, None, check, 0.0, None, None, None, None, None,
                                   flags=list(submission.flags))
        return PracticeOutcome(submission, submission.band, Evaluation.model_validate(submission.evaluation), check,
                               submission.evidence_weight, FeedbackCard.model_validate(submission.card) if submission.card else None,
                               submission.tip_text, submission.tip_key, submission.follow_up, None, flags=list(submission.flags))

    # ------------------------------------------------------------------ derived state

    @property
    def attempt_id_uuid(self) -> uuid.UUID:
        return uuid.UUID(str(self.attempt_id))

    @property
    def hints_used(self) -> int:
        return max((e.level for e in self.exposures if e.kind == "hint"), default=0)

    @property
    def reference_revealed(self) -> bool:
        return any(e.kind == "reference" for e in self.exposures)

    @property
    def main_submission(self) -> Submission | None:
        return next((s for s in reversed(self.submissions) if s.turn == 0), None)

    @property
    def submitted(self) -> bool:
        return self.main_submission is not None

    @property
    def band(self) -> Band | None:
        main = self.main_submission
        return main.band if main else None

    @property
    def evaluation(self) -> Evaluation | None:
        main = self.main_submission
        return Evaluation.model_validate(main.evaluation) if main and main.evaluation else None

    @property
    def revealed_before_submit(self) -> bool:
        """The reference was shown before the main answer that counts was accepted."""
        main = self.main_submission
        return main.reference_seen if main else self.reference_revealed

    @property
    def pending_follow_up(self) -> dict | None:
        """The follow-up question that is waiting for an answer, if any."""
        for turn in reversed(self.follow_up_turns):
            if turn.get("submission_revision") is None:
                return turn
            revision = turn["submission_revision"]
            submission = self.submissions[revision - 1]
            if submission.status == EvaluationStatus.FAILED:
                return turn
        return None

    # ------------------------------------------------------------------ before submitting

    def prompt(self) -> str:
        return generator.from_bank(self.question, self.ctx.language).question.question_text

    def next_hint(self) -> tuple[int, str] | None:
        """Bank hints, one level at a time (AI_Engine_Spec §6.3). Each one lowers the evidence weight."""
        if self.submitted or self.hints_used >= 3:
            return None
        level = self.hints_used + 1
        text = generator.bank_hint(self.question, level, self.ctx.language)
        if text is None:
            return None
        self._expose("hint", level)
        self._state(self.question.primary_skill).hint_level = level
        return level, text

    def hint_at(self, level: int) -> str | None:
        """Replay-safe read of a hint already exposed (for page refresh). Never advances exposure."""
        if 1 <= level <= self.hints_used:
            return generator.bank_hint(self.question, level, self.ctx.language)
        return None

    def reveal_reference(self) -> str:
        """Revealing is allowed at any time. Answers accepted afterwards produce no skill evidence (§2.9, §6.6)."""
        if not self.reference_revealed:
            self._expose("reference", 0)
        return self.question.text(self.ctx.language).reference_solution

    def _expose(self, kind: str, level: int) -> None:
        self.exposures.append(ExposureEvent(sequence=len(self.exposures) + 1, kind=kind, level=level, at=_now()))

    # ------------------------------------------------------------------ accept

    def _accept(self, answer, *, turn: int, idempotency_key: str | None) -> tuple[Submission, bool]:
        """Record the answer as a revision. Returns (submission, is_replay)."""
        answer_text = self._answer_text(answer)
        if not answer_text:
            raise PracticeError("validation", "the answer is empty")
        if len(answer_text) > MAX_ANSWER_CHARS:
            raise PracticeError("validation", f"the answer is longer than {MAX_ANSWER_CHARS} characters")
        key = idempotency_key or str(uuid.uuid4())

        existing = next((s for s in self.submissions if s.key == key), None)
        if existing is not None:
            if existing.answer != answer_text or existing.turn != turn:
                raise PracticeError("conflict", "this idempotency key was already used for a different answer")
            return existing, True

        for older in self.submissions:
            if older.turn == turn and "superseded" not in older.flags:
                older.flags = [*older.flags, "superseded"]         # never retried or scored again
        submission = Submission(
            revision=len(self.submissions) + 1, key=key, turn=turn, answer=answer_text,
            hints_seen=self.hints_used, reference_seen=self.reference_revealed,
            exposure_sequence=len(self.exposures), accepted_at=_now())
        self.submissions.append(submission)
        return submission, False

    # ------------------------------------------------------------------ submit

    async def submit(self, answer, *, idempotency_key: str | None = None, latency_ms: int | None = None,
                     revision_count: int | None = None) -> PracticeOutcome:
        """Accept the main answer and evaluate it. Idempotent per key; a second different answer is a conflict."""
        submission, replay = await self.accept(answer, idempotency_key=idempotency_key)
        if replay is not None:
            return replay
        return await self.evaluate(submission, latency_ms=latency_ms, revision_count=revision_count)

    async def submit_follow_up(self, answer, *, idempotency_key: str | None = None,
                               latency_ms: int | None = None) -> PracticeOutcome:
        submission, replay = await self.accept(answer, idempotency_key=idempotency_key, follow_up=True)
        if replay is not None:
            return replay
        return await self.evaluate(submission, latency_ms=latency_ms)

    async def accept(self, answer, *, idempotency_key: str | None = None,
                     follow_up: bool = False) -> tuple[Submission, PracticeOutcome | None]:
        """Step 1 of a submission: record the answer as a revision, before any model call.

        Returns (submission, None) for a new revision, or (submission, stored outcome) when the key was
        seen before. A caller that persists between the two steps can survive a crash mid-evaluation.
        """
        async with self._lock:
            existing = next((s for s in self.submissions if s.key == idempotency_key), None) if idempotency_key else None
            if follow_up:
                pending = self.pending_follow_up
                if existing is not None:
                    return existing, self._replay(existing, answer)
                if pending is None:
                    raise PracticeError("no_pending_follow_up", "there is no follow-up question to answer")
                submission, _ = self._accept(answer, turn=pending["turn"], idempotency_key=idempotency_key)
                pending["submission_revision"] = submission.revision
                return submission, None
            main = self.main_submission
            if main is not None and main.status != EvaluationStatus.FAILED:
                if existing is not None and existing.turn == 0:
                    return existing, self._replay(existing, answer)
                raise PracticeError("already_submitted",
                                    "this attempt already has an evaluated answer; start a new attempt to try again")
            submission, replay = self._accept(answer, turn=0, idempotency_key=idempotency_key)
            return submission, (self._replay(submission, answer) if replay else None)

    async def evaluate(self, submission: Submission, *, latency_ms: int | None = None,
                       revision_count: int | None = None) -> PracticeOutcome:
        """Step 2: evaluate an accepted revision. A revision already evaluated is replayed, never scored twice."""
        async with self._lock:
            if submission.status == EvaluationStatus.DONE or "superseded" in submission.flags:
                return self._replay(submission, submission.answer)
            if submission.status == EvaluationStatus.EVALUATING and not self._interrupted(submission):
                return self._replay(submission, submission.answer)          # in flight elsewhere: report, do not repeat
            return await self._evaluate(submission, latency_ms=latency_ms, revision_count=revision_count)

    async def retry_evaluation(self) -> PracticeOutcome:
        """Evaluate the latest failed submission again, with the same saved answer and the same exposure."""
        async with self._lock:
            failed = next((s for s in reversed(self.submissions)
                           if s.status == EvaluationStatus.FAILED and "superseded" not in s.flags), None)
            if failed is None:
                raise PracticeError("nothing_to_retry", "no submission is waiting for evaluation")
            return await self._evaluate(failed, latency_ms=None, revision_count=None)

    @staticmethod
    def _answer_text(answer) -> str:
        """The API sends {"text": ...} (or {"expression": ...} for checks); the CLI sends a string. Same answer either way."""
        if isinstance(answer, dict):
            answer = answer.get("text") or answer.get("expression") or ""
        return str(answer).strip()

    def _replay(self, submission: Submission, answer) -> PracticeOutcome:
        answer_text = self._answer_text(answer)
        if answer_text and answer_text != submission.answer:
            raise PracticeError("conflict", "this idempotency key was already used for a different answer")
        outcome = self._outcomes.get(submission.revision)
        if outcome is None:                       # accepted but never finished (crash mid-evaluation)
            return PracticeOutcome(submission, None, None, None, 0.0, None, None, None, None, None,
                                   flags=["evaluation_" + submission.status.value], replayed=True)
        # a copy: the stored outcome stays the record of the one real evaluation
        return dataclasses.replace(outcome, replayed=True)

    # ------------------------------------------------------------------ evaluate and score

    def _state(self, key: str) -> SkillState:
        if key not in self.skill_states:
            self.skill_states[key] = SkillState(key=key)
        state = self.skill_states[key]
        if state.k is None or state.c is None:
            prior = scores.skill_prior(seniority=self.ctx.seniority, params=self.ctx.params)
            state.k = state.k if state.k is not None else prior.k
            state.c = state.c if state.c is not None else prior.c
        return state

    @staticmethod
    def _record_usage(usage: list[UsageEvent], action: str, result) -> None:
        if getattr(result, "model", ""):
            usage.append(UsageEvent(action, result.model, result.usage, result.latency_ms))

    async def _evaluate(self, submission: Submission, *, latency_ms: int | None, revision_count: int | None) -> PracticeOutcome:
        ctx, question = self.ctx, self.question
        is_follow_up = submission.turn > 0
        usage: list[UsageEvent] = []
        submission.status = EvaluationStatus.EVALUATING
        submission.evaluating_since = _now()
        submission.attempts += 1
        if latency_ms is not None and latency_ms < 0:
            latency_ms = None

        primary = ctx.skills[question.primary_skill]
        state = self._state(primary.key)
        check = None
        if is_follow_up:
            turn = self.follow_up_turns[submission.turn - 1]
            difficulty = turn.get("difficulty") or question.difficulty
            result = await evaluator.evaluate(
                ctx.provider, language=ctx.language, difficulty=difficulty, answer=submission.answer,
                question_context=evaluator.follow_up_block(turn["question"], turn.get("expected_answer_outline", ""),
                                                           primary, difficulty),
                known_error_keys=set(), hint_level=state.hint_level, glossary=ctx.glossary)
        else:
            difficulty = question.difficulty
            check = checks.run_check(question.deterministic_check, submission.answer) if question.deterministic_check else None
            result = await evaluator.evaluate(
                ctx.provider, question_context=evaluator.question_block(question, ctx.language, primary),
                known_error_keys={e.key for e in question.common_errors}, language=ctx.language,
                difficulty=difficulty, answer=submission.answer, check=check, hint_level=submission.hints_seen,
                glossary=ctx.glossary)
        self._record_usage(usage, "evaluate", result)
        submission.evaluator_model = result.model or getattr(ctx.provider, "model", None) or None

        flags = list(result.flags)
        if self.language_fallback:
            flags.append("language_fallback_to_english")
        submission.check = check.model_dump(mode="json") if check else None
        if not result.ok:
            submission.status = EvaluationStatus.FAILED
            submission.evaluating_since = None
            submission.flags = flags + ["saved_without_evaluation"]
            outcome = PracticeOutcome(submission, None, None, check, 0.0, None, None, None, None, None,
                                      usage=usage, flags=submission.flags)
            self._outcomes[submission.revision] = outcome
            return outcome

        outcome = await self._score_and_respond(submission, result, check, difficulty, latency_ms, revision_count,
                                                usage, is_follow_up=is_follow_up)
        outcome.flags = list(dict.fromkeys([*flags, *outcome.flags]))
        submission.status = EvaluationStatus.DONE
        submission.evaluating_since = None
        submission.evaluated_at = _now()
        submission.band = outcome.band
        submission.evaluation = outcome.evaluation.model_dump()
        submission.flags = outcome.flags
        submission.evidence_weight = outcome.evidence_weight
        submission.card = outcome.card.model_dump() if outcome.card else None
        submission.tip_key, submission.tip_text, submission.follow_up = outcome.tip_key, outcome.tip_text, outcome.follow_up
        self._outcomes[submission.revision] = outcome
        return outcome

    async def _score_and_respond(self, submission: Submission, result: EvaluationResult, check: CheckResult | None,
                                 difficulty: int, latency_ms: int | None, revision_count: int | None,
                                 usage: list[UsageEvent], *, is_follow_up: bool) -> PracticeOutcome:
        ctx, question, params = self.ctx, self.question, self.ctx.params
        evaluation = scores.apply_check_result(result.evaluation, check, params)
        core = bool(set(evaluation.misconceptions) & question.core_misconception_keys)
        band = scores.classify_band(evaluation, core, params)
        self.misconceptions_hit = sorted(set(self.misconceptions_hit) | set(evaluation.misconceptions))

        primary_state = self._state(question.primary_skill)
        hint_level = submission.hints_seen if not is_follow_up else primary_state.hint_level
        # evidence is bound to what had been exposed when THIS revision was accepted; a generated
        # follow-up is new to everyone, so it carries neither the bank question's familiarity nor its exposure risk
        weight = scores.evidence_weight(
            self.evidence_mode, "new" if is_follow_up else self.familiarity, hint_level,
            "low" if is_follow_up else question.exposure_risk,
            revealed_before_submit=submission.reference_seen, params=params)

        # one metrics row per examined skill; secondary skills get evidence in proportion to their share
        links = [link for link in question.skills if link.primary] if is_follow_up else question.skills
        primary_share = next(link.weight for link in question.skills if link.primary)
        metrics = []
        for link in links:
            state = self._state(link.skill)
            skill_weight = round(min(weight, weight * link.weight / primary_share), 3)
            update = scores.update_scores(
                k_old=state.k, c_old=state.c, evaluation=evaluation, difficulty=difficulty,
                difficulty_ceiling=ctx.difficulty_ceiling, turns_on_skill=state.turns, hint_level=hint_level,
                latency_ms=latency_ms, revision_count=revision_count, weight=skill_weight, params=params)
            state.k, state.c = update.k_after, update.c_after
            scores.record_turn(state, difficulty=difficulty, band=band, evaluation=evaluation, hint_level=hint_level,
                               weight=skill_weight, core_misconception=core, archetype=question.archetype, params=params)
            catalog_skill = ctx.skills[link.skill]
            metrics.append({
                "mode": self.evidence_mode, "band": band.value, "subject_key": catalog_skill.subject, "skill_key": link.skill,
                "skill_source": "role", "skill_combined_weight": ctx.skill_weights.get(link.skill, link.weight),
                "skill_required_level": ctx.required_levels.get(link.skill, 2),
                "question_archetype": question.archetype.value, "difficulty_asked": difficulty,
                "evidence_weight": skill_weight, "check_passed": check.passed if check else None,
                "familiarity": "new" if is_follow_up else self.familiarity,
                "correctness": evaluation.correctness, "depth": evaluation.depth, "clarity": evaluation.clarity,
                "structure": evaluation.structure, "tradeoff_reasoning": evaluation.tradeoff_reasoning,
                "risk_awareness": evaluation.risk_awareness, "hedging_ratio": evaluation.hedging_ratio,
                "response_latency_ms": latency_ms, "revision_count": revision_count,
                "knowledge_score_before": update.k_before, "knowledge_score_after": update.k_after,
                "confidence_score_before": update.c_before, "confidence_score_after": update.c_after,
                "provisional_level_after": state.provisional_level, "hint_level": hint_level,
                "hint_delivered": hint_level > 0, "evaluator_model": result.model,
                "evaluator_version": result.prompt_version, "decision_engine_version": ENGINE_VERSION,
                "eval_latency_ms": result.latency_ms, "eval_flags": list(result.flags),
                "submission_revision": submission.revision,
            })

        # what next: the skill controller, limited to two follow-ups and one escalation
        decision, follow_up_text = None, None
        if self.mode == "deep" and len(self.follow_up_turns) < MAX_FOLLOW_UPS and weight > 0:
            controller = skill_controller.decide(
                primary_state, band=band, confidence=primary_state.c, depth=evaluation.depth,
                plan_skill=self.plan_skill, difficulty_ceiling=ctx.difficulty_ceiling, params=params)
            wants_second_escalation = controller.action == Action.ESCALATE and self._escalated
            if not controller.resolved and not wants_second_escalation:
                self._escalated |= controller.action == Action.ESCALATE
                action, next_difficulty, next_hint = controller.action, controller.next_difficulty, controller.hint_level
                if action == Action.HINT:
                    # hints escalate one level at a time, counting the ones already taken before submitting
                    if self.hints_used >= params.controller.max_hint_level:
                        action, next_hint = Action.STEP_BACK, 0
                        next_difficulty = max(self.plan_skill.min_difficulty, difficulty - params.controller.step_back_delta)
                    else:
                        next_hint = self.hints_used + 1
                        self._expose("hint", next_hint)
                    primary_state.hint_level = next_hint
                decision = Decision(
                    action=action, reason_code=controller.reason_code, target_subject=question.subject,
                    target_skill=controller.target_skill or question.primary_skill,
                    target_difficulty=next_difficulty, target_archetype=question.archetype,
                    probe_focus="; ".join(evaluation.key_points_missed[:2]) or None,
                    deliver_hint=action == Action.HINT, hint_level=next_hint)
                previous = [question.text(ctx.language).prompt, *[t["question"] for t in self.follow_up_turns]]
                generated = await generator.generate(
                    ctx.provider, decision, language=ctx.language, skill=ctx.skills.get(decision.target_skill),
                    question=question, last_question=previous[-1], last_answer_summary=evaluation.one_line_summary,
                    glossary=ctx.glossary, previous_questions=previous)
                self._record_usage(usage, "generate", generated)
                self._follow_up_difficulty = next_difficulty or difficulty
                follow_up_text = generated.question.question_text
                self.follow_up_turns.append({
                    "turn": len(self.follow_up_turns) + 1, "question": follow_up_text, "generated": True,
                    "source": generated.source, "action": action.value, "difficulty": self._follow_up_difficulty,
                    "expected_answer_outline": generated.question.expected_answer_outline,
                    "submission_revision": None, "created_at": _now()})
                metrics[0]["decision_action"] = action.value
                metrics[0]["decision_reason_code"] = controller.reason_code
                metrics[0]["difficulty_next"] = next_difficulty
            else:
                metrics[0]["decision_reason_code"] = controller.reason_code

        # the feedback card belongs to the main question; follow-ups get the tip and the next question only
        card = None
        if not is_follow_up:
            built = await feedback.build_card(
                ctx.provider, question=question, evaluation=evaluation, band=band, answer=submission.answer, check=check,
                language=ctx.language, skill_label=ctx.skills[question.primary_skill].label, glossary=ctx.glossary)
            self._record_usage(usage, "feedback", built)
            card = built.card

        tip_text, tip_key = await self._tip(evaluation, band, hint_level, check, usage)
        flags: list[str] = []
        if submission.reference_seen:
            flags.append("revealed_before_submit_no_evidence")
        return PracticeOutcome(submission, band, evaluation, check, weight, card, tip_text, tip_key, follow_up_text,
                               decision, metrics=metrics, usage=usage, flags=flags)

    async def _tip(self, evaluation: Evaluation, band: Band, hint_level: int, check: CheckResult | None,
                   usage: list[UsageEvent]) -> tuple[str | None, str | None]:
        ctx = self.ctx
        if not ctx.tips:
            return None, None
        state = self._state(self.question.primary_skill)
        signals = tips.signals_from(evaluation, band=band, archetype=self.question.archetype.value,
                                    hint_level=hint_level, confidence=state.c, self_confidence=self.self_confidence,
                                    mode=self.mode, check_passed=check.passed if check else None)
        # tips named by a matched common error come first; then the rule-matched library
        named = [e.tip_key for e in self.question.common_errors if e.key in evaluation.misconceptions and e.tip_key]
        pool = [t for t in ctx.tips if t.key in named] or ctx.tips
        turn = len(self.follow_up_turns)
        choice = tips.select_tip(pool, signals, turn_index=turn, last_delivered_turn=self._tip_turns,
                                 skill_key=self.question.primary_skill, role_family=ctx.role_family,
                                 timing="post_session")
        if choice is None and named:
            forced = next((t for t in ctx.tips if t.key in named), None)
            choice = tips.TipChoice(forced, "post_session", float(forced.severity)) if forced else None
        if choice is None:
            return None, None
        self._tip_turns[choice.tip.key] = turn
        placeholders = {"missed_point": (evaluation.key_points_missed or [""])[0],
                        "skill_label": ctx.skills[self.question.primary_skill].label}
        composed = await tips.compose(ctx.provider if ctx.polish_tips else None, choice, language=ctx.language,
                                      placeholders=placeholders)
        self._record_usage(usage, "tip", composed)         # metered like every other model call
        return composed.text, choice.tip.key

    # ------------------------------------------------------------------ what to persist

    def attempt_row(self, *, duration_ms: int | None = None) -> dict:
        """The fields of public.attempt this engine owns (Data_Models §14.2), plus the durable practice state."""
        main = self.main_submission
        return {
            "id": self.attempt_id, "question_key": self.question.key, "question_version": self.question.version,
            "mode": self.mode, "practice_language": self.ctx.language, "self_confidence_before": self.self_confidence,
            "answer": ({"text": main.answer, "revision": main.revision, "key": main.key, "status": main.status.value}
                       if main else None),
            "check_result": main.check if main else None,
            "evaluation": main.evaluation if main else None,
            "band": main.band.value if main and main.band else None,
            "hints_used": self.hints_used, "reference_revealed": self.reference_revealed,
            "revealed_before_submit": self.revealed_before_submit,
            "follow_up_turns": self.follow_up_turns, "misconceptions_hit": self.misconceptions_hit,
            "familiarity": self.familiarity, "evidence_mode": self.evidence_mode, "duration_ms": duration_ms,
            "tip_turns": dict(self._tip_turns),
            "submissions": [s.model_dump(mode="json") for s in self.submissions],
            "exposures": [e.model_dump(mode="json") for e in self.exposures],
        }
