"""One user action on a practice attempt, from request to durable result.

    load (short transaction)  ->  engine (may call the model, no transaction open)  ->  save (one transaction)

Rules the service enforces, independent of the HTTP layer:

* An attempt belongs to the user who started it; nothing else is ever returned.
* The daily attempt allowance is checked when an attempt starts and fails with `usage_limit`.
* An answer is SAVED before it is evaluated (accept, save, then evaluate, then save). A crash
  between the two saves leaves a revision that `restore()` marks failed and `retry` finishes.
* One action at a time per attempt in this process (a lock); across processes the database's
  unique idempotency key catches the rest, and a lost race is answered with the stored result.
* The skill profile is written with its version; a lost race there keeps the answer, marks the
  evaluation failed with `profile_conflict`, and lets the client retry.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from app.api.errors import ApiError
from app.engine import bank, next_question, plan_router, scores
from app.engine.catalog import Catalog
from app.engine.plan import merge_skill_sets
from app.engine.practice import (
    EvaluationStatus,
    ImageFetcher,
    PracticeAttempt,
    PracticeContext,
    PracticeError,
    PracticeOutcome,
    assessed_by,
)
from app.engine.providers import Provider
from app.repo.attempts import AlreadyEvaluated, DuplicateSubmissionKey, StoredAttempt
from app.repo.plans import OPEN, PlanItemRow, StoredPlan
from app.repo.profiles import LoadedProfile, StaleProfile, as_profile_skills
from app.repo.questions import CompanyTag, LoadedQuestion, QuestionDetail, QuestionSummary, detail
from app.repo.sightings import SightingsUnavailable, slugify
from app.repo.users import SENIORITIES, Goal
from app.schemas.api import (
    AttemptView,
    CardView,
    CheckView,
    CompanyView,
    FollowUpView,
    GoalView,
    HintView,
    JobTypeView,
    LabelledSkill,
    NextQuestionView,
    PlanItemView,
    PlanView,
    ProgramStartView,
    ProgramView,
    ProgressOverview,
    ProgressView,
    SkillProgress,
    SubjectProgress,
    SubmissionView,
    TimelinePoint,
    TipView,
)
from app.schemas.bank import BankQuestion, JobType
from app.schemas.engine import Archetype, Band, Evaluation, PlanSkill, SkillState
from app.services.store import Store

log = logging.getLogger("app.practice")

LANGUAGES = ("en", "he")
MODES = ("quick", "deep")
MIN_MINUTES_PER_DAY, MAX_MINUTES_PER_DAY, DEFAULT_MINUTES_PER_DAY = 5, 600, 30
PROGRAM_CARRY_DAYS = 3            # an item not done within 3 days of its day is dropped (the router re-adds the skill if it matters)
INTERVIEW_DURATIONS = (20, 30, 45)
PROGRAM_MESSAGES = {
    "en": {"no_goal": "Tell us what you are preparing for and the program builds itself.",
           "nothing_today": "Nothing is due today. Rest, or start tomorrow's first item early.",
           "no_question": "The bank has no reviewed question for this item yet; it was skipped."},
    "he": {"no_goal": "ספרו לנו לאיזה ראיון אתם מתכוננים, והתוכנית תיבנה מעצמה.",
           "nothing_today": "אין משהו להיום. מנוחה, או להתחיל את הפריט הראשון של מחר מוקדם.",
           "no_question": "במאגר אין עדיין שאלה מאושרת לפריט הזה; הוא דולג."},
}

# the level in words, never a percentage: what the overview card shows (Shaked, 2026-09-23)
LEVEL_WORDS = {
    "en": ["Getting started", "Awareness", "Foundational", "Proficient", "Advanced", "Expert"],
    "he": ["בתחילת הדרך", "מודעות", "בסיס", "שליטה", "מתקדם", "מומחה"],
}
MESSAGES = {
    "en": {
        "none": "Your first answer is the hardest one. Pick a question and go.",
        "few": "{answered} answers in. Every one of them teaches the coach what to ask you next.",
        "some": "{answered} answers and {strong} strong ones. The picture of your strengths is forming.",
        "many": "{answered} answers, {strong} strong. You are building real interview stamina.",
    },
    "he": {
        "none": "התשובה הראשונה היא הקשה ביותר. בחרו שאלה וצאו לדרך.",
        "few": "{answered} תשובות עד כה. כל אחת מהן מלמדת את המאמן מה לשאול אתכם הלאה.",
        "some": "{answered} תשובות, {strong} מהן חזקות. תמונת החוזקות שלכם מתבהרת.",
        "many": "{answered} תשובות, {strong} חזקות. אתם בונים סיבולת אמיתית לאינטרוויו.",
    },
}


@dataclass
class ServiceConfig:
    role: str = "digital-hardware-engineer"
    company: str = "generic"
    default_language: str = "en"
    daily_attempt_limit: int = 30
    polish_tips: bool = False
    # The coach suggests only questions a person has reviewed and published. With nothing published there is
    # no suggestion at all, never an unreviewed one (Shaked, 2026-09-21). False only for development and tests.
    suggest_reviewed_only: bool = True


class PracticeService:
    def __init__(self, store: Store, catalog: Catalog, provider: Provider, config: ServiceConfig | None = None, *,
                 image_fetcher: ImageFetcher | None = None):
        self.store, self.catalog, self.provider = store, catalog, provider
        self.config = config or ServiceConfig()
        self.image_fetcher = image_fetcher                 # None: photos are stored but not shown to the evaluator
        self._locks: dict[uuid.UUID, asyncio.Lock] = {}
        self._plans: dict[tuple[str, str | None], tuple[dict[str, int], dict[str, float], int, list[PlanSkill]]] = {}

    # ------------------------------------------------------------------ questions

    async def list_questions(self, *, language: str, subject: str | None = None, job: str | None = None,
                             company: str | None = None) -> list[QuestionSummary]:
        """The library, enriched: job types, company tags, and (with `job`) relevance order and filter."""
        language = self._language(language)
        job_type = self._job_type(job)
        async with self.store.transaction() as tx:
            rows = await tx.list_questions(language=language, subject=subject)
            if company:
                allowed = await tx.question_ids_for_company(slugify(company))
                rows = [r for r in rows if r.id in allowed]
            tags = await tx.sightings_for([r.id for r in rows]) if rows else {}
        return self._enrich(rows, tags, job_type)

    def _job_type(self, key: str | None) -> JobType | None:
        if not key:
            return None
        job = self.catalog.job_types.get(key)
        if job is None:
            raise ApiError("validation", f"unknown job type {key!r}; see /v1/job-types")
        return job

    def _job_types_for(self, question: BankQuestion) -> list[str]:
        """A question belongs to every job type that does not play down its primary skill."""
        return [key for key, job in self.catalog.job_types.items() if job.weight(question.primary_skill) >= 1.0]

    @staticmethod
    def _relevance(question: BankQuestion, job: JobType) -> float:
        return round(sum(link.weight * job.weight(link.skill) for link in question.skills), 3)

    def _enrich(self, rows: list[QuestionSummary], tags: dict[str, list[dict]], job: JobType | None) -> list[QuestionSummary]:
        out = []
        for row in rows:
            question = self.catalog.questions.get(row.key)
            update = {"companies": [CompanyTag(**t) for t in tags.get(row.id, [])]}
            if question is not None:
                update["job_types"] = self._job_types_for(question)
                if job is not None:
                    if job.key not in update["job_types"]:
                        continue
                    update["relevance"] = self._relevance(question, job)
            elif job is not None:
                continue
            out.append(row.model_copy(update=update))
        if job is not None:
            out.sort(key=lambda r: (-(r.relevance or 0.0), r.difficulty, r.key))
        return out

    def job_types(self, *, language: str) -> list[JobTypeView]:
        language = self._language(language)
        return [JobTypeView(key=j.key, label=j.text("label", language), description=j.text("description", language))
                for j in self.catalog.job_types.values()]

    async def companies(self) -> list[CompanyView]:
        async with self.store.transaction() as tx:
            return [CompanyView(**row) for row in await tx.companies()]

    async def add_sighting(self, user_id: uuid.UUID, *, company: str, key: str | None = None,
                           question_id: uuid.UUID | None = None) -> list[CompanyTag]:
        """'I saw this question at company X'. Returns the question's company tags afterwards."""
        async with self.store.transaction() as tx:
            loaded = await tx.load_question(key=key, question_id=question_id)
            if loaded is None:
                raise ApiError("not_found", "this question does not exist or is not available")
            try:
                await tx.add_sighting(question_id=str(loaded.id), user_id=user_id, company=company)
            except SightingsUnavailable as exc:
                raise ApiError("temporarily_unavailable", str(exc), status=503) from exc
            except ValueError as exc:
                raise ApiError("validation", str(exc)) from exc
            tags = await tx.sightings_for([str(loaded.id)])
        return [CompanyTag(**t) for t in tags.get(str(loaded.id), [])]

    # ------------------------------------------------------------------ the goal

    async def get_goal(self, user_id: uuid.UUID, *, language: str | None = None) -> GoalView:
        async with self.store.transaction() as tx:
            goal = await tx.load_goal(user_id)
        return self._goal_view(goal, self._language(language))

    async def save_goal(self, user_id: uuid.UUID, *, job_type: str | None, interview_date: date | None,
                        minutes_per_day: int | None, seniority: str | None, language: str | None = None) -> GoalView:
        self._job_type(job_type)
        if minutes_per_day is not None and not MIN_MINUTES_PER_DAY <= minutes_per_day <= MAX_MINUTES_PER_DAY:
            raise ApiError("validation", f"minutes_per_day must be between {MIN_MINUTES_PER_DAY} and {MAX_MINUTES_PER_DAY}")
        if seniority is not None and seniority not in SENIORITIES:
            raise ApiError("validation", f"seniority must be one of {', '.join(SENIORITIES)}")
        goal = Goal(job_type=job_type, interview_date=interview_date, minutes_per_day=minutes_per_day, seniority=seniority)
        async with self.store.transaction() as tx:
            await tx.save_goal(user_id, goal)
            await tx.deactivate_plan(user_id)                       # a new goal means a new program
            stored = await tx.load_goal(user_id)                    # what the row says, not what the request said
        return self._goal_view(stored, self._language(language))

    def _goal_view(self, goal: Goal, language: str) -> GoalView:
        job = self.catalog.job_types.get(goal.job_type) if goal.job_type else None
        return GoalView(job_type=job.key if job else None, job_type_label=job.text("label", language) if job else None,
                        interview_date=goal.interview_date.isoformat() if goal.interview_date else None,
                        days_to_interview=goal.days_to_interview(), minutes_per_day=goal.minutes_per_day,
                        seniority=goal.seniority, complete=goal.complete)

    async def get_question(self, *, language: str, key: str | None = None,
                           question_id: uuid.UUID | None = None) -> QuestionDetail:
        async with self.store.transaction() as tx:
            loaded = await tx.load_question(key=key, question_id=question_id)
            if loaded is None:
                raise ApiError("not_found", "this question does not exist or is not available")
            tags = await tx.sightings_for([str(loaded.id)])
        view = detail(loaded, self._language(language))
        return view.model_copy(update={"job_types": self._job_types_for(loaded.question),
                                       "companies": [CompanyTag(**t) for t in tags.get(str(loaded.id), [])]})

    # ------------------------------------------------------------------ attempts

    async def start(self, user_id: uuid.UUID, *, question_key: str | None = None, question_id: uuid.UUID | None = None,
                    mode: str = "deep", language: str | None = None, self_confidence: int | None = None) -> AttemptView:
        if mode not in MODES:
            raise ApiError("validation", f"mode must be one of {', '.join(MODES)}")
        language = self._language(language)
        for _try in range(2):                                        # a profile race (two tabs) is redone once
            try:
                async with self.store.transaction() as tx:
                    started = await tx.started_today(user_id)
                    if started >= self.config.daily_attempt_limit:
                        raise ApiError("usage_limit", f"you have started {started} attempts today; the daily limit is "
                                                      f"{self.config.daily_attempt_limit}. Come back tomorrow.")
                    loaded = await tx.load_question(key=question_key, question_id=question_id)
                    if loaded is None:
                        raise ApiError("not_found", "this question does not exist or is not available")
                    profile = await tx.load_profile(user_id)
                    goal = await tx.load_goal(user_id)
                    seniority = goal.seniority or await tx.user_seniority(user_id) or "student"
                    ctx = self._context(seniority, language, goal.job_type)
                    try:
                        attempt = PracticeAttempt(ctx, loaded.question, profile.states, mode=mode, familiarity="new",
                                                  self_confidence=self_confidence)
                    except PracticeError as exc:
                        raise ApiError(exc.code, str(exc)) from exc
                    row = attempt.attempt_row()
                    await tx.save_attempt(user_id=user_id, question_id=loaded.id, row=row, revisions=set())
                    await tx.save_profile(profile, self._primary_state(attempt, profile), attempt_id=attempt.attempt_id_uuid)
                break
            except StaleProfile:
                continue
        else:
            raise ApiError("conflict", "your profile was updated by another request; try again")
        stored = StoredAttempt(id=attempt.attempt_id_uuid, user_id=user_id, question_id=loaded.id,
                               question_key=loaded.question.key, started_at=_now(), row=row)
        return self._view(attempt, stored, loaded, language)

    async def get(self, user_id: uuid.UUID, attempt_id: uuid.UUID) -> AttemptView:
        attempt, stored, loaded, _ = await self._load(user_id, attempt_id)
        return self._view(attempt, stored, loaded, stored.row["practice_language"])

    async def next_hint(self, user_id: uuid.UUID, attempt_id: uuid.UUID) -> tuple[HintView | None, AttemptView]:
        async with self._lock(attempt_id):
            for _try in range(2):
                attempt, stored, loaded, profile = await self._load(user_id, attempt_id)
                result = attempt.next_hint()
                if result is None:
                    break
                try:
                    async with self.store.transaction() as tx:
                        await tx.save_attempt(user_id=user_id, question_id=stored.question_id, row=attempt.attempt_row(),
                                              revisions=set())
                        await tx.save_profile(profile, self._primary_state(attempt, profile), attempt_id=attempt_id)
                    break
                except StaleProfile:
                    continue
            else:
                raise ApiError("conflict", "your profile was updated by another request; try again")
            hint = HintView(level=result[0], text=result[1]) if result else None
            return hint, self._view(attempt, stored, loaded, stored.row["practice_language"])

    async def reveal_reference(self, user_id: uuid.UUID, attempt_id: uuid.UUID) -> tuple[str, AttemptView]:
        async with self._lock(attempt_id):
            attempt, stored, loaded, _ = await self._load(user_id, attempt_id)
            was_revealed = attempt.reference_revealed
            text = attempt.reveal_reference()
            if not was_revealed:
                async with self.store.transaction() as tx:
                    await tx.save_attempt(user_id=user_id, question_id=stored.question_id, row=attempt.attempt_row(),
                                          revisions=set())
            return text, self._view(attempt, stored, loaded, stored.row["practice_language"])

    async def submit(self, user_id: uuid.UUID, attempt_id: uuid.UUID, answer, *, idempotency_key: str | None,
                     latency_ms: int | None = None, revision_count: int | None = None,
                     follow_up_turn: int | None = None) -> tuple[SubmissionView, AttemptView]:
        async with self._lock(attempt_id):
            attempt, stored, loaded, profile = await self._load(user_id, attempt_id)
            language = stored.row["practice_language"]
            if follow_up_turn is not None:
                pending = attempt.pending_follow_up
                if pending is None or pending["turn"] != follow_up_turn:
                    raise ApiError("no_pending_follow_up", "this follow-up is not the one waiting for an answer")
            try:
                submission, replay = await attempt.accept(answer, idempotency_key=idempotency_key,
                                                          follow_up=follow_up_turn is not None)
            except PracticeError as exc:
                raise ApiError(exc.code, str(exc)) from exc
            if replay is not None:
                return self._submission_view(replay.submission, replay), self._view(attempt, stored, loaded, language)

            if submission.visual and submission.visual.images:
                async with self.store.transaction() as tx:
                    if not await tx.validate_answer_images(user_id, attempt_id, submission.visual.images):
                        raise ApiError("validation", "an answer image is missing or does not belong to this attempt")

            # 1. the answer is durable before any model call
            known = len(stored.row["submissions"])
            try:
                async with self.store.transaction() as tx:
                    await tx.save_attempt(user_id=user_id, question_id=stored.question_id, row=attempt.attempt_row(),
                                          revisions={submission.revision}, known_revisions=known)
            except DuplicateSubmissionKey:
                # another process accepted a revision first: answer with what it stored, or say so
                attempt, stored, loaded, profile = await self._load(user_id, attempt_id)
                if not any(s.key == idempotency_key for s in attempt.submissions):
                    raise ApiError("conflict", "another answer was accepted on this attempt a moment ago; "
                                              "reload the attempt") from None
                try:
                    existing, replay = await attempt.accept(answer, idempotency_key=idempotency_key,
                                                            follow_up=follow_up_turn is not None)
                except PracticeError as exc:
                    raise ApiError(exc.code, str(exc)) from exc
                return self._submission_view(existing, replay), self._view(attempt, stored, loaded, language)

            # 2. evaluate: model calls happen here, with no transaction open
            outcome = await attempt.evaluate(submission, latency_ms=latency_ms, revision_count=revision_count)

            # 3. everything the evaluation produced, in one transaction
            attempt, stored, loaded, outcome = await self._persist_outcome(user_id, attempt, stored, loaded, profile, outcome)
            return (self._submission_view(outcome.submission, outcome, attempt.next_question),
                    self._view(attempt, stored, loaded, language))

    async def retry(self, user_id: uuid.UUID, attempt_id: uuid.UUID) -> tuple[SubmissionView, AttemptView]:
        async with self._lock(attempt_id):
            attempt, stored, loaded, profile = await self._load(user_id, attempt_id)
            try:
                outcome = await attempt.retry_evaluation()
            except PracticeError as exc:
                raise ApiError(exc.code, str(exc)) from exc
            attempt, stored, loaded, outcome = await self._persist_outcome(user_id, attempt, stored, loaded, profile, outcome)
            return (self._submission_view(outcome.submission, outcome, attempt.next_question),
                    self._view(attempt, stored, loaded, stored.row["practice_language"]))

    async def _persist_outcome(self, user_id: uuid.UUID, attempt: PracticeAttempt, stored: StoredAttempt,
                               loaded: LoadedQuestion, profile: LoadedProfile, outcome: PracticeOutcome
                               ) -> tuple[PracticeAttempt, StoredAttempt, LoadedQuestion, PracticeOutcome]:
        """Write everything one evaluation produced, in one transaction.

        Two races are handled without a second model call: if the skill profile moved meanwhile
        (another attempt of the same user finished first), the scores are re-applied on top of the
        fresh profile; if another process finished evaluating this very revision first, its stored
        result is returned instead of ours.
        """
        changed = {outcome.submission.revision}
        if outcome.status == EvaluationStatus.DONE and outcome.band is not None:
            await self._suggest_next(user_id, attempt, outcome)
        for _try in range(2):
            try:
                async with self.store.transaction() as tx:
                    if outcome.status == EvaluationStatus.DONE and outcome.evaluation is not None:
                        await tx.save_profile(profile, self._touched_states(attempt, outcome), attempt_id=attempt.attempt_id_uuid)
                        await tx.record_metrics(user_id=user_id, attempt_id=attempt.attempt_id_uuid, metrics=outcome.metrics,
                                                seniority=profile.seniority)
                        if outcome.tip_key and outcome.tip_text:
                            await tx.record_tip(attempt_id=attempt.attempt_id_uuid, tip_key=outcome.tip_key,
                                                skill_key=attempt.question.primary_skill, text=outcome.tip_text)
                    if outcome.usage:
                        await tx.record_usage(user_id=user_id, attempt_id=attempt.attempt_id_uuid,
                                              usage_rows=[u.as_row(attempt.mode) for u in outcome.usage])
                    await tx.save_attempt(user_id=user_id, question_id=stored.question_id, row=attempt.attempt_row(),
                                          revisions=changed, known_revisions=len(attempt.submissions))
                    if outcome.status == EvaluationStatus.DONE and outcome.band is not None and outcome.submission.turn == 0:
                        await self._complete_program_item(tx, user_id, attempt_id=attempt.attempt_id_uuid,
                                                          skills=[link.skill for link in attempt.question.skills])
                return attempt, stored, loaded, outcome
            except StaleProfile as exc:
                log.warning("profile moved during attempt %s (%s): re-applying the scores", attempt.attempt_id, exc)
                async with self.store.transaction() as tx:
                    fresh = await tx.load_profile(user_id)
                fresh.seniority = profile.seniority
                self._rescore(attempt, outcome, fresh)
                profile = fresh
            except AlreadyEvaluated:
                log.warning("revision %s of attempt %s was evaluated elsewhere first; replaying it",
                            outcome.submission.revision, attempt.attempt_id)
                if outcome.usage:                                    # our model calls still happened and cost money
                    async with self.store.transaction() as tx:
                        await tx.record_usage(user_id=user_id, attempt_id=attempt.attempt_id_uuid,
                                              usage_rows=[u.as_row(attempt.mode) for u in outcome.usage])
                attempt, stored, loaded, _ = await self._load(user_id, attempt.attempt_id_uuid)
                theirs = next(s for s in attempt.submissions if s.revision == outcome.submission.revision)
                return attempt, stored, loaded, attempt._outcome_from(theirs)

        # the profile keeps moving: keep the answer, undo this run's side effects, let a retry score it
        log.error("profile conflict twice on attempt %s; leaving the evaluation for retry", attempt.attempt_id)
        submission = outcome.submission
        self._undo_follow_up(attempt, outcome)
        submission.status = EvaluationStatus.FAILED
        submission.evaluating_since = None
        submission.flags = [*submission.flags, "profile_conflict"]
        submission.follow_up = None
        outcome.flags = list(submission.flags)
        async with self.store.transaction() as tx:
            if outcome.usage:
                await tx.record_usage(user_id=user_id, attempt_id=attempt.attempt_id_uuid,
                                      usage_rows=[u.as_row(attempt.mode) for u in outcome.usage])
            await tx.save_attempt(user_id=user_id, question_id=stored.question_id, row=attempt.attempt_row(),
                                  revisions=changed, known_revisions=len(attempt.submissions))
        return attempt, stored, loaded, outcome

    async def _suggest_next(self, user_id: uuid.UUID, attempt: PracticeAttempt, outcome: PracticeOutcome) -> None:
        """Decide what to practise next from this evaluation; stored on the attempt so a refresh shows the same."""
        language = attempt.ctx.language
        async with self.store.transaction() as tx:
            servable = await tx.list_questions(language=language)
            seen = await tx.seen_question_keys(user_id)
        if self.config.suggest_reviewed_only:
            servable = [s for s in servable if s.reviewed]
        candidates = [self.catalog.questions[s.key] for s in servable if s.key in self.catalog.questions]
        question = attempt.question
        # what was hard: the bank's own explanation of each known mistake this attempt hit, and the skill it undermines
        text = question.translations.get(language) or question.translations.get("en")
        explanations = text.common_errors if text else {}
        hit = set(attempt.misconceptions_hit)
        struggles = [next_question.Struggle(key=e.key, skill=e.skill or question.primary_skill,
                                            text=explanations.get(e.key, ""), core=e.core)
                     for e in question.common_errors if e.key in hit and explanations.get(e.key)]
        # the whole attempt decides, not only the answer just scored: main band + every follow-up band
        main = attempt.main_submission
        main_band = main.band if main is not None and main.band is not None else outcome.band
        follow_up_bands = [s.band for s in attempt.submissions if s.turn > 0 and s.band is not None]
        suggestion = next_question.suggest(
            current=question, band=main_band, states=attempt.skill_states, candidates=candidates, seen=seen,
            required_levels=attempt.ctx.required_levels, skill_weights=attempt.ctx.skill_weights,
            skill_labels=self.catalog.skill_labels(), language=language, difficulty_ceiling=attempt.ctx.difficulty_ceiling,
            struggles=struggles, follow_up_bands=follow_up_bands)
        if suggestion is None:
            attempt.next_question = None
            return
        picked = next(s for s in servable if s.key == suggestion.key)
        attempt.next_question = {"key": suggestion.key, "title": picked.title, "subject": picked.subject,
                                 "skill": suggestion.skill, "difficulty": suggestion.difficulty, "why": suggestion.why,
                                 "reason": suggestion.reason, "focus": suggestion.focus}

    def _rescore(self, attempt: PracticeAttempt, outcome: PracticeOutcome, fresh: LoadedProfile) -> None:
        """Re-apply one evaluation's scores on top of a profile that moved (pure functions, no model call)."""
        ctx, params, evaluation = attempt.ctx, attempt.ctx.params, outcome.evaluation
        old_states, attempt.skill_states = attempt.skill_states, fresh.states
        core = bool(set(evaluation.misconceptions) & attempt.question.core_misconception_keys)
        for m in outcome.metrics:
            state = attempt._state(m["skill_key"])
            update = scores.update_scores(
                k_old=state.k, c_old=state.c, evaluation=evaluation, difficulty=m["difficulty_asked"],
                difficulty_ceiling=ctx.difficulty_ceiling, turns_on_skill=state.turns, hint_level=m["hint_level"],
                latency_ms=m["response_latency_ms"], revision_count=m["revision_count"], weight=m["evidence_weight"],
                params=params)
            state.k, state.c = update.k_after, update.c_after
            scores.record_turn(state, difficulty=m["difficulty_asked"], band=Band(m["band"]), evaluation=evaluation,
                               hint_level=m["hint_level"], weight=m["evidence_weight"], core_misconception=core,
                               archetype=Archetype(m["question_archetype"]), params=params)
            m.update(knowledge_score_before=update.k_before, knowledge_score_after=update.k_after,
                     confidence_score_before=update.c_before, confidence_score_after=update.c_after,
                     provisional_level_after=state.provisional_level)
        # this attempt's controller decisions (status, budget, hint level) belong to this attempt
        primary = attempt.question.primary_skill
        if primary in old_states:
            new_primary, old_primary = attempt._state(primary), old_states[primary]
            for name in ("status", "budget", "current_difficulty", "hint_level", "partial_count",
                         "level3_hint_difficulty", "resolved_reason"):
                setattr(new_primary, name, getattr(old_primary, name))

    @staticmethod
    def _undo_follow_up(attempt: PracticeAttempt, outcome: PracticeOutcome) -> None:
        """Drop the follow-up turn (and its hint exposure) this evaluation appended, so a retry can create them anew."""
        if not outcome.follow_up or not attempt.follow_up_turns:
            return
        last = attempt.follow_up_turns[-1]
        if last.get("submission_revision") is None and last.get("question") == outcome.follow_up:
            attempt.follow_up_turns.pop()
            if last.get("action") == "hint" and attempt.exposures and attempt.exposures[-1].kind == "hint":
                attempt.exposures.pop()

    # ------------------------------------------------------------------ progress

    async def progress(self, user_id: uuid.UUID, *, language: str | None = None) -> ProgressView:
        language = self._language(language)
        async with self.store.transaction() as tx:
            profile = await tx.load_profile(user_id)
            recent = await tx.recent_attempts(user_id, limit=10)
            history = await tx.recent_attempts(user_id, limit=60)        # the plan's memory: scored answers, today included
            started = await tx.started_today(user_id)
            goal = await tx.load_goal(user_id)
            seniority = goal.seniority or await tx.user_seniority(user_id) or "student"
            bands = await tx.band_counts(user_id)
            daily = await tx.daily_bands(user_id)
            servable = await tx.list_questions(language=language)
        required, weights, _, plan_skills = self._plan(seniority, goal.job_type)
        now = datetime.now(UTC)
        skills = []
        for key, state in sorted(profile.states.items()):
            catalog_skill = self.catalog.skills.get(key)
            if catalog_skill is None:
                continue
            level, _ = scores.questioned_level(state)
            status = scores.evidence_status(state, required.get(key, 2))
            history = profile.level_history.get(key, [])
            last_level = history[-2]["level"] if len(history) >= 2 else None
            trend = ("new" if state.turns == 0 else "stable" if last_level is None or level == last_level
                     else "improving" if (level or 0) > last_level else "declining")
            retention = profile.retention.get(key, {})
            last = profile.last_assessed.get(key)
            value = scores.loyalty(last, now) if status.value != "not_assessed" else None
            skills.append(SkillProgress(
                key=key, label=catalog_skill.label, subject=catalog_skill.subject or "", level=level, status=status.value,
                trend=trend, required_level=required.get(key, 2),
                assessments=sum(1 for t in state.history if t.evidence_weight > 0),
                last_assessed_at=last.isoformat() if last else (history[-1]["at"] if history else None),
                retention_due_at=retention.get("due").isoformat() if retention.get("due") else None,
                loyalty=value, needs_refresh=level is not None and scores.needs_refresh(value)))
        subjects = self._subjects(skills, required, weights, bands, servable)
        today = date.today()
        async with self.store.transaction() as tx:
            program = await self._ensure_program(tx, user_id, profile, plan_skills, required, servable, history, goal, seniority,
                                                 language, today)
        return ProgressView(skills=skills, subjects=subjects, recent=recent, attempts_today=started,
                            daily_limit=self.config.daily_attempt_limit,
                            overview=self._overview(skills, plan_skills, bands, language),
                            timeline=self._timeline(daily, profile),
                            plan=self._plan_view(program, goal, today),
                            goal=self._goal_view(goal, language))

    # ------------------------------------------------------------------ the saved program

    async def program(self, user_id: uuid.UUID, *, language: str | None = None) -> ProgramView:
        """What is due today, carried-forward items first, and the one item to start now."""
        language = self._language(language)
        today = date.today()
        async with self.store.transaction() as tx:
            profile = await tx.load_profile(user_id)
            goal = await tx.load_goal(user_id)
            seniority = goal.seniority or await tx.user_seniority(user_id) or "student"
            servable = await tx.list_questions(language=language)
            history = await tx.recent_attempts(user_id, limit=60)
            required, _, _, plan_skills = self._plan(seniority, goal.job_type)
            program = await self._ensure_program(tx, user_id, profile, plan_skills, required, servable, history, goal, seniority,
                                                 language, today)
        return self._program_view(program, goal, today)

    async def start_program_item(self, user_id: uuid.UUID, *, item_id: uuid.UUID | None = None,
                                 language: str | None = None) -> ProgramStartView:
        """Open the item (the next due one unless given): a practice attempt on a bank question chosen for the item's
        skill and the user's level, or the interview lobby for a simulation item."""
        language = self._language(language)
        today = date.today()
        view = await self.program(user_id, language=language)
        texts = PROGRAM_MESSAGES.get(language, PROGRAM_MESSAGES["en"])
        if not view.goal_complete:
            return ProgramStartView(kind="nothing", message=texts["no_goal"])
        item = next((i for i in view.today if item_id is None or i.id == str(item_id)), None) or view.next
        if item is None:
            return ProgramStartView(kind="nothing", message=texts["nothing_today"])
        if item.mode == "simulation":
            duration = min(INTERVIEW_DURATIONS, key=lambda d: abs(d - item.minutes))
            return ProgramStartView(kind="interview", item=item, interview_duration_min=duration)
        mode = "deep" if item.mode == "deep" else "quick"
        async with self.store.transaction() as tx:
            profile = await tx.load_profile(user_id)
            goal = await tx.load_goal(user_id)
            seniority = goal.seniority or await tx.user_seniority(user_id) or "student"
            servable = await tx.list_questions(language=language)
            seen = await tx.seen_question_keys(user_id)
        required, _, ceiling, _ = self._plan(seniority, goal.job_type)
        question = self._question_for(item, profile, servable, seen, required, ceiling, mode, language)
        if question is None:
            async with self.store.transaction() as tx:
                await tx.update_plan_item(uuid.UUID(item.id), status="skipped")
            return ProgramStartView(kind="nothing", item=item, message=texts["no_question"])
        attempt = await self.start(user_id, question_key=question.key, mode=mode, language=language)
        async with self.store.transaction() as tx:
            await tx.link_attempt_to_plan_item(uuid.UUID(attempt.id), uuid.UUID(item.id))
            await tx.update_plan_item(uuid.UUID(item.id), status="started")
        del today
        return ProgramStartView(kind="attempt", item=item.model_copy(update={"status": "started"}), attempt=attempt)

    def _question_for(self, item: PlanItemView, profile: LoadedProfile, servable, seen: set[str], required: dict[str, int],
                      ceiling: int, mode: str, language: str) -> BankQuestion | None:
        """The same choice the coach makes after an answer: the item's skill, the user's level, unseen and reviewed first."""
        pool = self._servable_pool(servable)
        reviewed_only = self.config.suggest_reviewed_only
        for skill_key in [s.key for s in item.skills]:
            state = profile.states.get(skill_key)
            target = min(ceiling, next_question._difficulty_now(state, required.get(skill_key, 2)))
            for seen_keys, window in ((seen, 1), (seen, 3), (set(), 9)):
                for try_mode in (mode, "quick", "deep", "simulation"):
                    picked = bank.select_question(pool, skill=skill_key, difficulty=target, mode=try_mode, language=language,
                                                  seen_keys=seen_keys, allow_in_review=not reviewed_only, require_parity=False,
                                                  difficulty_window=window)
                    if picked is not None:
                        return picked.question
        return None

    def _servable_pool(self, servable) -> list[BankQuestion]:
        """Catalog questions the coach may use, carrying the database's state (trial/published), not the seed file's."""
        pool = []
        for row in servable:
            question = self.catalog.questions.get(row.key)
            if question is None or not (row.reviewed or not self.config.suggest_reviewed_only):
                continue
            if question.status != row.status:
                question = question.model_copy(update={"status": row.status})
            pool.append(question)
        return pool

    async def _ensure_program(self, tx, user_id: uuid.UUID, profile: LoadedProfile, plan_skills: list[PlanSkill],
                              required: dict[str, int], servable, history: list[dict], goal: Goal, seniority: str,
                              language: str, today: date) -> StoredPlan:
        """Today's plan. The program is rebuilt every day from the fresh profile (so a level that went stale or rose
        overnight changes the plan), and the open items of earlier days that are still fresh lead it (carried
        forward); an item more than PROGRAM_CARRY_DAYS past its day is dropped, the router re-adds the skill if it
        still matters. Within one day the saved plan is reused, so a started item stays started."""
        plan = await tx.load_active_plan(user_id)
        minutes = goal.minutes_per_day or DEFAULT_MINUTES_PER_DAY
        carried: list[PlanItemRow] = []
        if plan is not None:
            if plan.week_start == today and plan.minutes_per_day == minutes and plan.interview_date == goal.interview_date:
                return plan
            for item in plan.items:
                planned_for = plan.week_start + timedelta(days=item.day_index)
                if item.status in OPEN and planned_for <= today and (today - planned_for).days <= PROGRAM_CARRY_DAYS:
                    carried.append(item)
        routed = self._router_items(profile, plan_skills, required, servable, history, goal, language, today)
        items: list[dict] = []
        taken: set[tuple[str, tuple[str, ...]]] = set()
        for item in carried:
            signature = (item.mode, tuple(item.skills))
            if signature in taken:
                continue
            taken.add(signature)
            items.append({"day_index": 0, "mode": item.mode, "skills": item.skills, "reason": item.reason,
                          "minutes": item.minutes, "created_at": item.created_at})
        labels = self.catalog.skill_labels()
        for planned in routed:
            signature = (planned.activity.mode, tuple(planned.activity.skills))
            if signature in taken:
                continue
            taken.add(signature)
            items.append({"day_index": planned.day_index, "mode": planned.activity.mode, "skills": list(planned.activity.skills),
                          "reason": plan_router.reason_text(planned.activity, language, labels),
                          "minutes": planned.activity.estimated_minutes})
        return await tx.create_plan(user_id=user_id, role_slug=self.config.role, seniority=seniority, week_start=today,
                                    minutes_per_day=minutes, interview_date=goal.interview_date, items=items)

    async def _complete_program_item(self, tx, user_id: uuid.UUID, *, attempt_id: uuid.UUID | None = None,
                                     session_id: uuid.UUID | None = None, skills: list[str] | None = None,
                                     today: date | None = None) -> None:
        """Tick the program item this attempt or interview fulfilled: the one it was started from, else the earliest
        open item due by today on one of the same skills (a practice item) or a simulation item (an interview)."""
        plan = await tx.load_active_plan(user_id)
        if plan is None:
            return
        today_index = plan.day_index_of(today or date.today())
        linked = await tx.attempt_plan_item(attempt_id) if attempt_id is not None else None
        open_items = [i for i in plan.items if i.status in OPEN and i.day_index <= max(today_index, 0)]
        chosen = next((i for i in open_items if i.id == linked), None)
        if chosen is None:
            wanted = set(skills or [])
            if session_id is not None:
                fitting = [i for i in open_items if i.mode == "simulation"]
            else:
                fitting = [i for i in open_items if i.mode != "simulation" and wanted & set(i.skills)]
            chosen = min(fitting, key=lambda i: (i.day_index, i.created_at), default=None)
        if chosen is None:
            return
        fields = {"status": "done"}
        if attempt_id is not None:
            fields["completed_attempt_id"] = attempt_id
        if session_id is not None:
            fields["completed_session_id"] = session_id
        await tx.update_plan_item(chosen.id, **fields)

    def _plan_view(self, plan: StoredPlan, goal: Goal, today: date) -> PlanView:
        labels = self.catalog.skill_labels()
        offset = plan.day_index_of(today)                       # 0 for today's plan; a stale plan shifts by the days elapsed
        views = []
        for item in sorted(plan.items, key=lambda i: (i.day_index, i.created_at.date() >= plan.week_start, i.created_at)):
            views.append(PlanItemView(
                id=str(item.id), day_index=item.day_index - offset,
                date=(plan.week_start + timedelta(days=item.day_index)).isoformat(), mode=item.mode,
                skills=[LabelledSkill(key=k, label=labels.get(k, k)) for k in item.skills], minutes=item.minutes,
                reason=item.reason, done=item.status == "done", status=item.status,
                carried=item.created_at.date() < plan.week_start))          # created for an earlier plan: carried forward
        return PlanView(items=views, minutes_per_day=plan.minutes_per_day, days_to_interview=goal.days_to_interview(today),
                        interview_date=goal.interview_date.isoformat() if goal.interview_date else None,
                        generated_for=plan.week_start.isoformat(), saved=True)

    def _program_view(self, plan: StoredPlan, goal: Goal, today: date) -> ProgramView:
        view = self._plan_view(plan, goal, today)
        today_items = [i for i in view.items if i.day_index == 0 and i.status in OPEN]
        today_items.sort(key=lambda i: (not i.carried, i.mode == "simulation"))     # carried first, interviews last
        done_today = sum(1 for i in view.items if i.day_index == 0 and i.status == "done")
        return ProgramView(plan=view, today=today_items, next=today_items[0] if today_items else None, done_today=done_today,
                           minutes_due_today=sum(i.minutes for i in today_items), goal_complete=goal.complete)

    @staticmethod
    def _level_rank(skills: list[SkillProgress]) -> tuple[int, int]:
        """(rank 0..5, assessed count): the average assessed level rounded, 0 when nothing is assessed yet."""
        assessed = [s.level for s in skills if s.status == "assessed" and s.level and not s.needs_refresh]
        if not assessed:
            return 0, 0
        return max(1, min(5, round(sum(assessed) / len(assessed)))), len(assessed)

    def _overview(self, skills: list[SkillProgress], plan_skills: list[PlanSkill], bands: dict[str, dict[str, int]],
                  language: str) -> ProgressOverview:
        totals = {b: sum(per.get(b, 0) for per in bands.values()) for b in ("STRONG", "PARTIAL", "WEAK")}
        answered = sum(totals.values())
        plan_keys = {p.key for p in plan_skills if p.assessment_mode.value == "questioned"}
        in_plan = [s for s in skills if s.key in plan_keys] or skills
        rank, assessed = self._level_rank(in_plan)
        to_refresh = sum(1 for s in in_plan if s.needs_refresh)
        words = LEVEL_WORDS.get(language, LEVEL_WORDS["en"])
        texts = MESSAGES.get(language, MESSAGES["en"])
        kind = "none" if answered == 0 else "few" if answered < 5 else "some" if answered < 20 else "many"
        return ProgressOverview(answered=answered, strong=totals["STRONG"], partial=totals["PARTIAL"], weak=totals["WEAK"],
                                skills_assessed=assessed, skills_to_refresh=to_refresh, skills_total=len(plan_keys),
                                level=words[rank], level_rank=rank,
                                message=texts[kind].format(answered=answered, strong=totals["STRONG"]))

    @staticmethod
    def _timeline(daily: list[dict], profile: LoadedProfile) -> list[TimelinePoint]:
        """One point per practice day: answers by band and the average level across skills at the end of that day."""
        history = []
        for key, entries in profile.level_history.items():
            for e in entries:
                when = e.get("at")
                if when and e.get("level"):
                    history.append((datetime.fromisoformat(when).date().isoformat(), key, int(e["level"])))
        history.sort()
        points = []
        for day in daily:
            levels: dict[str, int] = {}
            for when, key, level in history:
                if when <= day["day"]:
                    levels[key] = level
            strong, partial, weak = day.get("STRONG", 0), day.get("PARTIAL", 0), day.get("WEAK", 0)
            points.append(TimelinePoint(day=day["day"], answered=strong + partial + weak, strong=strong, partial=partial,
                                        weak=weak, level=round(sum(levels.values()) / len(levels), 2) if levels else None))
        return points

    def _router_items(self, profile: LoadedProfile, plan_skills: list[PlanSkill], required: dict[str, int], servable,
                      recent: list[dict], goal: Goal, language: str, today: date) -> list[plan_router.PlannedItem]:
        """The Plan Router's week, from today until the interview (or seven days), within the user's minutes."""
        minutes = goal.minutes_per_day or DEFAULT_MINUTES_PER_DAY
        days_left = goal.days_to_interview(today)
        pool = self._servable_pool(servable)
        coverage = bank.coverage_by_skill(pool, language=language, allow_in_review=not self.config.suggest_reviewed_only,
                                          require_parity=False)
        scored = [r for r in recent if r.get("band")]
        history = [plan_router.RecentActivity(mode=r.get("mode") or "quick", band=r.get("band")) for r in scored]
        del language
        return plan_router.weekly_plan(plan=plan_skills, profile=as_profile_skills(profile, required), week_start=today,
                                       minutes_per_day=minutes, bank_coverage=coverage, days_to_interview=days_left,
                                       recent=history)

    def _subjects(self, skills: list[SkillProgress], required: dict[str, int], weights: dict[str, float],
                  bands: dict[str, dict[str, int]], servable) -> list[SubjectProgress]:
        """Roll the per-skill picture up to subjects: what the charts draw."""
        by_key = {s.key: s for s in skills}
        available: dict[str, int] = {}
        for q in servable:
            available[q.subject] = available.get(q.subject, 0) + 1
        out = []
        for subject_key, subject in sorted(self.catalog.domains.items()):
            plan_skills = [k for k in required if self.catalog.skills.get(k) and self.catalog.skills[k].subject == subject_key]
            if not plan_skills and subject_key not in bands:
                continue
            levels = {str(n): 0 for n in range(1, 6)}
            assessed, started_n, level_sum = 0, 0, 0
            for k in plan_skills:
                s = by_key.get(k)
                if s is None:
                    continue
                if s.assessments:
                    started_n += 1
                if s.status == "assessed" and s.level:
                    assessed += 1
                    level_sum += s.level
                    levels[str(s.level)] += 1
            subject_bands = {b: bands.get(subject_key, {}).get(b, 0) for b in ("STRONG", "PARTIAL", "WEAK")}
            out.append(SubjectProgress(
                key=subject_key, label=subject.label, skills_total=len(plan_skills), skills_assessed=assessed,
                skills_started=started_n, levels=levels, average_level=round(level_sum / assessed, 2) if assessed else None,
                bands=subject_bands, attempts=sum(subject_bands.values()),
                weight=round(sum(weights.get(k, 0.0) for k in plan_skills), 3), questions_available=available.get(subject_key, 0)))
        return out

    # ------------------------------------------------------------------ internals

    def _language(self, language: str | None) -> str:
        language = language or self.config.default_language
        if language not in LANGUAGES:
            raise ApiError("validation", f"language must be one of {', '.join(LANGUAGES)}")
        return language

    @asynccontextmanager
    async def _lock(self, attempt_id: uuid.UUID):
        """One action at a time per attempt. The lock is forgotten once nobody holds or waits for it,
        so the table does not grow with every attempt the process has ever seen."""
        lock = self._locks.setdefault(attempt_id, asyncio.Lock())
        try:
            async with lock:
                yield
        finally:
            if not lock.locked() and not getattr(lock, "_waiters", None) and self._locks.get(attempt_id) is lock:
                del self._locks[attempt_id]

    def _plan(self, seniority: str, job_type: str | None = None
              ) -> tuple[dict[str, int], dict[str, float], int, list[PlanSkill]]:
        """(required levels, skill weights, difficulty ceiling, plan rows) for a seniority and a job type.

        The job type does not add skills: it multiplies the role's skill weights (verification leans on testbenches
        and debugging, embedded on bit manipulation ...), so the plan, the next-question suggestion and the weekly
        plan lean the same way. An unknown job type is ignored, never an error here."""
        job = self.catalog.job_types.get(job_type) if job_type else None
        key = (seniority, job.key if job else None)
        if key not in self._plans:
            role = self.catalog.roles[self.config.role]
            company = self.catalog.companies[self.config.company]
            if seniority not in role.seniority_profiles:
                seniority = next(iter(role.seniority_profiles))
            rows = role.skill_set
            if job is not None:
                rows = [row.model_copy(update={"weight": row.weight * job.weight(row.skill)}) for row in rows]
            plan = merge_skill_sets(role_rows=rows, company_rows=company.skill_set, focus_skill_keys=[],
                                    company_weight_share=company.company_weight_share, seniority=seniority,
                                    planned_duration_min=45, catalog=self.catalog.leaf_skills)
            profile = role.seniority_profiles[seniority]
            self._plans[key] = ({s.key: s.required_level for s in plan}, {s.key: s.combined_weight for s in plan},
                                profile.difficulty_ceiling, plan)
        return self._plans[key]

    def _context(self, seniority: str, language: str, job_type: str | None = None) -> PracticeContext:
        required, weights, ceiling, _ = self._plan(seniority, job_type)
        role = self.catalog.roles[self.config.role]
        return PracticeContext(provider=self.provider, skills=self.catalog.leaf_skills, language=language,
                               seniority=seniority, difficulty_ceiling=ceiling, required_levels=required,
                               skill_weights=weights, tips=list(self.catalog.tips.values()), glossary=self.catalog.glossary,
                               role_family=role.family, polish_tips=self.config.polish_tips,
                               image_fetcher=self.image_fetcher)

    async def _load(self, user_id: uuid.UUID, attempt_id: uuid.UUID
                    ) -> tuple[PracticeAttempt, StoredAttempt, LoadedQuestion, LoadedProfile]:
        try:
            return await self._load_once(user_id, attempt_id)
        except Exception as exc:                                   # noqa: BLE001 - only the lost-connection family
            from app.api.errors import is_connection_error
            if not is_connection_error(exc):
                raise
            log.warning("database connection dropped while loading attempt %s; retrying once", attempt_id)
            return await self._load_once(user_id, attempt_id)     # reads only: safe to repeat

    async def _load_once(self, user_id: uuid.UUID, attempt_id: uuid.UUID
                         ) -> tuple[PracticeAttempt, StoredAttempt, LoadedQuestion, LoadedProfile]:
        async with self.store.transaction() as tx:
            stored = await tx.load_attempt(attempt_id, user_id=user_id)
            if stored is None:
                raise ApiError("not_found", "this attempt does not exist")
            loaded = await tx.load_question(question_id=stored.question_id)
            if loaded is None:
                raise ApiError("not_found", "the question of this attempt is no longer available")
            profile = await tx.load_profile(user_id)
            goal = await tx.load_goal(user_id)
            seniority = goal.seniority or await tx.user_seniority(user_id) or "student"
        profile.seniority = seniority
        ctx = self._context(seniority, stored.row["practice_language"], goal.job_type)
        attempt = PracticeAttempt.restore(ctx, loaded.question, profile.states, stored.row)
        return attempt, stored, loaded, profile

    @staticmethod
    def _primary_state(attempt: PracticeAttempt, profile: LoadedProfile) -> dict[str, SkillState]:
        key = attempt.question.primary_skill
        return {key: profile.states[key]}

    @staticmethod
    def _touched_states(attempt: PracticeAttempt, outcome: PracticeOutcome) -> dict[str, SkillState]:
        keys = {m["skill_key"] for m in outcome.metrics} | {attempt.question.primary_skill}
        return {key: attempt.skill_states[key] for key in keys if key in attempt.skill_states}

    # ------------------------------------------------------------------ views

    @staticmethod
    def _next_view(raw: dict | None) -> NextQuestionView | None:
        return NextQuestionView.model_validate(raw) if raw else None

    @staticmethod
    def _submission_view(submission, outcome: PracticeOutcome | None = None, next_question: dict | None = None) -> SubmissionView:
        evaluation = Evaluation.model_validate(submission.evaluation) if submission.evaluation else None
        weight = outcome.evidence_weight if outcome is not None else submission.evidence_weight
        check = None
        if submission.check:
            check = CheckView(type=submission.check.get("type", ""), passed=submission.check.get("passed"),
                              detail=submission.check.get("detail", ""),
                              mismatches=list(submission.check.get("mismatches") or [])[:8])
        return SubmissionView(
            revision=submission.revision, key=submission.key, turn=submission.turn, answer=submission.answer, visual=submission.visual,
            status="evaluating" if submission.status == EvaluationStatus.PENDING else submission.status.value,
            accepted_at=submission.accepted_at, evaluated_at=submission.evaluated_at,
            band=submission.band.value if submission.band else None,
            summary=evaluation.one_line_summary if evaluation else None,
            key_points_hit=list(evaluation.key_points_hit) if evaluation else [],
            key_points_missed=list(evaluation.key_points_missed) if evaluation else [],
            check=check, card=CardView.model_validate(submission.card) if submission.card else None,
            tip=TipView(key=submission.tip_key, text=submission.tip_text) if submission.tip_key and submission.tip_text else None,
            follow_up=submission.follow_up,
            assessed_by="unassessed" if "visual_review_pending" in submission.flags else assessed_by(submission.evaluator_model),
            model=submission.evaluator_model if assessed_by(submission.evaluator_model) == "model" else None,
            hints_seen=submission.hints_seen, reference_seen=submission.reference_seen,
            evidence="none" if submission.status != EvaluationStatus.DONE or weight <= 0 else "full" if weight >= 1 else "reduced",
            flags=list(submission.flags), replayed=bool(outcome.replayed) if outcome is not None else False,
            next_question=PracticeService._next_view(next_question))

    def _view(self, attempt: PracticeAttempt, stored: StoredAttempt, loaded: LoadedQuestion, language: str) -> AttemptView:
        by_revision = {s.revision: s for s in attempt.submissions}
        main = attempt.main_submission
        follow_ups = []
        for turn in attempt.follow_up_turns:
            sub = by_revision.get(turn.get("submission_revision")) if turn.get("submission_revision") else None
            follow_ups.append(FollowUpView(turn=turn["turn"], question=turn["question"], action=turn.get("action", ""),
                                           created_at=turn.get("created_at", ""),
                                           submission=self._submission_view(sub) if sub else None))
        pending = attempt.pending_follow_up
        pending_view = next((f for f in follow_ups if f.turn == pending["turn"]), None) if pending else None
        latest_any = attempt.submissions[-1] if attempt.submissions else None
        if latest_any is not None and latest_any.status in (EvaluationStatus.PENDING, EvaluationStatus.EVALUATING):
            status = "evaluating"                    # main or follow-up: something is being scored right now
        elif main is None:
            status = "in_progress"
        elif main.status == EvaluationStatus.DONE:
            status = "in_progress" if pending is not None else "done"
        else:
            status = main.status.value
        latest = attempt.submissions[-1] if attempt.submissions else None
        return AttemptView(
            id=attempt.attempt_id, question=detail(loaded, language), mode=attempt.mode, language=language,
            self_confidence_before=attempt.self_confidence, status=status, started_at=stored.started_at.isoformat(),
            hints=[HintView(level=level, text=attempt.hint_at(level)) for level in range(1, attempt.hints_used + 1)],
            hints_remaining=max(0, min(3, len(loaded.question.text(language).hints)) - attempt.hints_used) if main is None else 0,
            reference=attempt.question.text(language).reference_solution if attempt.reference_revealed else None,
            submission=self._submission_view(main) if main else None, follow_ups=follow_ups, pending_follow_up=pending_view,
            can_submit=main is None or main.status == EvaluationStatus.FAILED,
            can_retry=latest is not None and latest.status == EvaluationStatus.FAILED,
            next_question=self._next_view(attempt.next_question))


def _now() -> datetime:
    return datetime.now(UTC)
