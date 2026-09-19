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
from datetime import UTC, datetime

from app.api.errors import ApiError
from app.engine import scores
from app.engine.catalog import Catalog
from app.engine.plan import merge_skill_sets
from app.engine.practice import (
    EvaluationStatus,
    PracticeAttempt,
    PracticeContext,
    PracticeError,
    PracticeOutcome,
    assessed_by,
)
from app.engine.providers import Provider
from app.repo.attempts import AlreadyEvaluated, DuplicateSubmissionKey, StoredAttempt
from app.repo.profiles import LoadedProfile, StaleProfile
from app.repo.questions import LoadedQuestion, QuestionDetail, QuestionSummary, detail
from app.schemas.api import (
    AttemptView,
    CardView,
    CheckView,
    FollowUpView,
    HintView,
    ProgressView,
    SkillProgress,
    SubmissionView,
    TipView,
)
from app.schemas.engine import Archetype, Band, Evaluation, SkillState
from app.services.store import Store

log = logging.getLogger("app.practice")

LANGUAGES = ("en", "he")
MODES = ("quick", "deep")


@dataclass
class ServiceConfig:
    role: str = "digital-hardware-engineer"
    company: str = "generic"
    default_language: str = "en"
    daily_attempt_limit: int = 30
    polish_tips: bool = False


class PracticeService:
    def __init__(self, store: Store, catalog: Catalog, provider: Provider, config: ServiceConfig | None = None):
        self.store, self.catalog, self.provider = store, catalog, provider
        self.config = config or ServiceConfig()
        self._locks: dict[uuid.UUID, asyncio.Lock] = {}
        self._plans: dict[str, tuple[dict[str, int], dict[str, float], int]] = {}

    # ------------------------------------------------------------------ questions

    async def list_questions(self, *, language: str, subject: str | None = None) -> list[QuestionSummary]:
        async with self.store.transaction() as tx:
            return await tx.list_questions(language=self._language(language), subject=subject)

    async def get_question(self, *, language: str, key: str | None = None,
                           question_id: uuid.UUID | None = None) -> QuestionDetail:
        async with self.store.transaction() as tx:
            loaded = await tx.load_question(key=key, question_id=question_id)
        if loaded is None:
            raise ApiError("not_found", "this question does not exist or is not available")
        return detail(loaded, self._language(language))

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
                    seniority = await tx.user_seniority(user_id) or "student"
                    ctx = self._context(seniority, language)
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
            return self._submission_view(outcome.submission, outcome), self._view(attempt, stored, loaded, language)

    async def retry(self, user_id: uuid.UUID, attempt_id: uuid.UUID) -> tuple[SubmissionView, AttemptView]:
        async with self._lock(attempt_id):
            attempt, stored, loaded, profile = await self._load(user_id, attempt_id)
            try:
                outcome = await attempt.retry_evaluation()
            except PracticeError as exc:
                raise ApiError(exc.code, str(exc)) from exc
            attempt, stored, loaded, outcome = await self._persist_outcome(user_id, attempt, stored, loaded, profile, outcome)
            return self._submission_view(outcome.submission, outcome), self._view(attempt, stored, loaded,
                                                                                    stored.row["practice_language"])

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
        async with self.store.transaction() as tx:
            profile = await tx.load_profile(user_id)
            recent = await tx.recent_attempts(user_id, limit=10)
            started = await tx.started_today(user_id)
            seniority = await tx.user_seniority(user_id) or "student"
        required, _, _ = self._plan(seniority)
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
            skills.append(SkillProgress(
                key=key, label=catalog_skill.label, subject=catalog_skill.subject or "", level=level, status=status.value,
                trend=trend, required_level=required.get(key, 2),
                assessments=sum(1 for t in state.history if t.evidence_weight > 0),
                last_assessed_at=history[-1]["at"] if history else None,
                retention_due_at=retention.get("due").isoformat() if retention.get("due") else None))
        return ProgressView(skills=skills, recent=recent, attempts_today=started,
                            daily_limit=self.config.daily_attempt_limit)

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

    def _plan(self, seniority: str) -> tuple[dict[str, int], dict[str, float], int]:
        if seniority not in self._plans:
            role = self.catalog.roles[self.config.role]
            company = self.catalog.companies[self.config.company]
            if seniority not in role.seniority_profiles:
                seniority = next(iter(role.seniority_profiles))
            plan = merge_skill_sets(role_rows=role.skill_set, company_rows=company.skill_set, focus_skill_keys=[],
                                    company_weight_share=company.company_weight_share, seniority=seniority,
                                    planned_duration_min=45, catalog=self.catalog.leaf_skills)
            profile = role.seniority_profiles[seniority]
            self._plans[seniority] = ({s.key: s.required_level for s in plan}, {s.key: s.combined_weight for s in plan},
                                      profile.difficulty_ceiling)
        return self._plans[seniority]

    def _context(self, seniority: str, language: str) -> PracticeContext:
        required, weights, ceiling = self._plan(seniority)
        role = self.catalog.roles[self.config.role]
        return PracticeContext(provider=self.provider, skills=self.catalog.leaf_skills, language=language,
                               seniority=seniority, difficulty_ceiling=ceiling, required_levels=required,
                               skill_weights=weights, tips=list(self.catalog.tips.values()), glossary=self.catalog.glossary,
                               role_family=role.family, polish_tips=self.config.polish_tips)

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
            seniority = await tx.user_seniority(user_id) or "student"
        profile.seniority = seniority
        ctx = self._context(seniority, stored.row["practice_language"])
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
    def _submission_view(submission, outcome: PracticeOutcome | None = None) -> SubmissionView:
        evaluation = Evaluation.model_validate(submission.evaluation) if submission.evaluation else None
        weight = outcome.evidence_weight if outcome is not None else submission.evidence_weight
        check = None
        if submission.check:
            check = CheckView(type=submission.check.get("type", ""), passed=submission.check.get("passed"),
                              detail=submission.check.get("detail", ""))
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
            assessed_by="unassessed" if submission.visual else assessed_by(submission.evaluator_model),
            model=submission.evaluator_model if assessed_by(submission.evaluator_model) == "model" else None,
            hints_seen=submission.hints_seen, reference_seen=submission.reference_seen,
            evidence="none" if submission.status != EvaluationStatus.DONE or weight <= 0 else "full" if weight >= 1 else "reduced",
            flags=list(submission.flags), replayed=bool(outcome.replayed) if outcome is not None else False)

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
            can_retry=latest is not None and latest.status == EvaluationStatus.FAILED)


def _now() -> datetime:
    return datetime.now(UTC)
