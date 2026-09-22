"""Mock interviews: the session engine (subject router + skill controller) driven over a store.

    start -> first question | answer -> evaluate -> scores -> next decision -> next question ... -> END -> report

Rules that matter here:
* Questions come from the bank only, and by default only from questions a person has reviewed and
  published (`reviewed_only`). A plan skill without a reviewed question is dropped from the interview;
  with none left, the interview cannot start (`no_reviewed_questions`). Nothing is generated.
* Like a real interview, bands and summaries stay hidden until the session is over; the report shows them.
* Every turn is persisted before and after the model call; a refresh or a crash never loses an answer, and a
  turn is scored exactly once (same idempotency key = replay, different key = 409).
* The candidate's skill profile continues through the interview: session skill states start from the
  profile's k/c and history and are written back after every scored turn.
"""

from __future__ import annotations

import asyncio
import copy
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.api.errors import ApiError
from app.engine import bank, checks, evaluator, generator, reporter, subject_router
from app.engine.catalog import Catalog
from app.engine.plan import merge_skill_sets
from app.engine.practice import UsageEvent
from app.engine.providers import Provider
from app.engine.reporter import ReportData
from app.engine.session import SessionEngine
from app.engine.skill_controller import ControllerResult
from app.repo.profiles import LoadedProfile, StaleProfile
from app.repo.sessions import StoredSession
from app.schemas.api import (
    CheckView,
    FitView,
    HintView,
    InterviewPlanSkill,
    InterviewReportView,
    InterviewTurnView,
    InterviewView,
    LabelledSkill,
    SkillReportView,
)
from app.schemas.bank import BankQuestion
from app.schemas.engine import (
    Action,
    AssessmentMode,
    Decision,
    PlanSkill,
    SessionState,
    SkillState,
    SkillStatus,
)
from app.services.store import Store

log = logging.getLogger("app.interview")

LANGUAGES = ("en", "he")
DURATIONS = (20, 30, 45)
MAX_TURNS = 40
_PLACEHOLDER = re.compile(r"\{\{\s*\w+\s*\}\}")


@dataclass
class InterviewConfig:
    role: str = "digital-hardware-engineer"
    company: str = "generic"
    default_language: str = "en"
    daily_limit: int = 5                        # interviews a user may start per UTC day
    reviewed_only: bool = True                  # bank questions that a person reviewed and published; never generated
    allow_hints: bool = True                    # coach mode: the candidate may ask for a hint (costs struggle budget)
    narrative: bool = True                      # write the report narrative with the model; a plain report otherwise


class InterviewService:
    def __init__(self, store: Store, catalog: Catalog, provider: Provider, config: InterviewConfig | None = None):
        self.store, self.catalog, self.provider = store, catalog, provider
        self.config = config or InterviewConfig()
        self._locks: dict[uuid.UUID, asyncio.Lock] = {}
        self._plans: dict[tuple[str, int], tuple[list[PlanSkill], int, int]] = {}
        self.clock = lambda: datetime.now(UTC)        # tests replace it to move the interview clock
        self._question_ids: dict[str, str] = {}       # question key -> database id, filled when the pool is listed

    def _stamp(self) -> str:
        return self.clock().isoformat()

    # ------------------------------------------------------------------ public API

    async def start(self, user_id: uuid.UUID, *, duration_min: int = 30, language: str | None = None) -> InterviewView:
        language = self._language(language)
        if duration_min not in DURATIONS:
            raise ApiError("validation", f"duration_min must be one of {', '.join(map(str, DURATIONS))}")
        async with self.store.transaction() as tx:
            started = await tx.sessions_started_today(user_id)
            if started >= self.config.daily_limit:
                raise ApiError("usage_limit", f"you have started {started} interviews today; the limit is "
                               f"{self.config.daily_limit}", headers={"Retry-After": "3600"})
            profile = await tx.load_profile(user_id)
            seniority = await tx.user_seniority(user_id) or "student"
            servable = await tx.list_questions(language=language)
        pool = self._pool(servable)
        plan, ceiling, baseline = self._plan(seniority, duration_min)
        plan = self._covered(plan, pool, language)
        priors = {k: (s.k, s.c) for k, s in profile.states.items() if s.k is not None and s.c is not None}
        state = subject_router.init_session_state(plan, seniority=seniority, baseline_difficulty=baseline,
                                                  difficulty_ceiling=ceiling, planned_duration_min=duration_min,
                                                  priors=priors)
        self._continue_histories(state, profile)
        engine = self._engine(plan, state)
        decision, question = self._open(engine, plan, state, engine.start(), pool, seen=set(), language=language)
        if question is None:
            raise ApiError("no_reviewed_questions", "the bank has no reviewed question to open this interview with")

        now = self._stamp()
        session_id = uuid.uuid4()
        wrapper = {"engine": state.model_dump(mode="json"), "metrics": [], "notes": {}, "flags": [], "ended_early": False,
                   "narrative": None, "narrative_source": None}
        row = {"id": str(session_id), "seniority": seniority, "baseline_difficulty": baseline, "difficulty_ceiling": ceiling,
               "status": "in_progress", "turn_count": 1, "hints_used": 0, "hints_requested_by_user": 0,
               "started_at": now, "ended_at": None, "state": wrapper,
               "config": {"language": language, "duration_min": duration_min, "role": self.config.role,
                          "company": self.config.company, "reviewed_only": self.config.reviewed_only,
                          "plan": [p.model_dump(mode="json") for p in plan]}}
        turns = [self._new_turn(0, decision, question, language, now)]
        async with self.store.transaction() as tx:
            await tx.save_session(user_id=user_id, row=row, turns=turns, plan=row["config"]["plan"],
                                  role_slug=self.config.role, company_slug=self.config.company)
        return self._view(StoredSession(id=session_id, user_id=user_id, row=row, turns=turns), state)

    async def get(self, user_id: uuid.UUID, session_id: uuid.UUID) -> InterviewView:
        stored, _, state, _, _ = await self._load(user_id, session_id)
        return self._view(stored, state)

    async def list(self, user_id: uuid.UUID, *, limit: int = 20) -> list[dict]:
        async with self.store.transaction() as tx:
            return await tx.list_sessions(user_id, limit=limit)

    async def answer(self, user_id: uuid.UUID, session_id: uuid.UUID, turn_index: int, answer, *,
                     idempotency_key: str, latency_ms: int | None = None) -> tuple[InterviewTurnView, InterviewView]:
        async with self._lock(session_id):
            stored, plan, state, engine, profile = await self._load(user_id, session_id)
            row, turns, language = stored.row, stored.turns, stored.row["config"]["language"]
            if row["status"] != "in_progress":
                raise ApiError("conflict", "this interview is over")
            turn = next((t for t in turns if t["turn_index"] == turn_index), None)
            if turn is None:
                raise ApiError("not_found", "no such question in this interview")
            meta = turn["question_generation_meta"]
            if meta.get("status") == "done" or turn is not turns[-1]:
                if meta.get("idempotency_key") == idempotency_key:            # the same click again: same result
                    return self._turn_view(turn, language, revealed=row["status"] == "completed"), self._view(stored, state)
                raise ApiError("already_submitted", "this question was already answered")
            if meta.get("status") == "evaluating" and meta.get("idempotency_key") not in (None, idempotency_key):
                raise ApiError("conflict", "this answer is being evaluated")
            text = answer.get("text", "") if isinstance(answer, dict) else str(answer or "")
            text = text.strip()
            if not text:
                raise ApiError("validation", "an answer is required (say what you would try, even if unsure)")
            if len(text) > 20_000:
                raise ApiError("validation", "the answer is too long (20,000 characters at most)")
            question = self.catalog.questions[turn["question_key"]]

            # 1. keep the answer before the model is called
            now = self._stamp()
            turn["answer_text"] = text
            turn["answer_submitted_at"] = now
            meta.update(status="evaluating", idempotency_key=idempotency_key, evaluating_since=now)
            await self._persist(user_id, row, [turn], state=state)

            # 2. check + evaluate
            check = (await asyncio.to_thread(checks.run_check, question.deterministic_check, text)
                     if question.deterministic_check else None)
            skill = self.catalog.skills[question.primary_skill]
            result = await evaluator.evaluate(
                self.provider, question_context=evaluator.question_block(question, language, skill),
                known_error_keys={e.key for e in question.common_errors}, language=language,
                difficulty=turn["difficulty"], answer=text, check=check, hint_level=meta.get("hint_level", 0),
                glossary=self.catalog.glossary)
            usage_rows = ([UsageEvent("evaluate", result.model, result.usage, result.latency_ms).as_row("simulation")]
                          if result.model else [])
            turn["check_result"] = check.model_dump(mode="json") if check else None
            if not result.ok:
                meta.update(status="failed", flags=list(result.flags), evaluating_since=None)
                await self._persist(user_id, row, [turn], state=state, usage_rows=usage_rows)
                return self._turn_view(turn, language, revealed=False), self._view(stored, state)

            # 3. scores and the next decision
            engine.core_misconception_keys = question.core_misconception_keys
            # the interview clock runs from the moment the question was shown until the verdict is in,
            # thinking time and evaluation wait alike, as it would with a human interviewer
            asked_at = datetime.fromisoformat(turn["asked_at"])
            elapsed_ms = max(0, int((self.clock() - asked_at).total_seconds() * 1000))
            outcome = engine.process_turn(
                result.evaluation, archetype=question.archetype, check=check, latency_ms=latency_ms,
                familiarity="new", exposure_risk=question.exposure_risk, turn_elapsed_ms=elapsed_ms, mode="simulation")
            evaluation = outcome.evaluation
            metrics = {**outcome.metrics, "evaluator_model": result.model, "evaluator_version": result.prompt_version,
                       "eval_latency_ms": result.latency_ms, "eval_flags": list(result.flags)}
            wrapper = row["state"]
            wrapper["metrics"].append(metrics)
            notes = wrapper["notes"].setdefault(question.primary_skill, {"hit": [], "missed": []})
            notes["hit"].extend(evaluation.key_points_hit[:3])
            notes["missed"].extend(evaluation.key_points_missed[:3])
            meta.update(status="done", band=outcome.band.value, summary=evaluation.one_line_summary,
                        key_points_hit=list(evaluation.key_points_hit), key_points_missed=list(evaluation.key_points_missed),
                        evaluation=evaluation.model_dump(mode="json"), evidence_weight=outcome.evidence_weight,
                        evaluator_model=result.model, flags=list(result.flags), evaluated_at=self._stamp(), evaluating_since=None,
                        action_after=outcome.decision.action.value, subject_switch=outcome.decision.subject_switch)

            # 4. the next question, or the end
            changed = [turn]
            decision = outcome.decision
            if decision.action != Action.END and len(turns) < MAX_TURNS:
                pool = await self._pool_for(language)
                decision, next_question = self._open(engine, plan, state, decision, pool,
                                                     seen={t["question_key"] for t in turns}, language=language)
                if next_question is not None:
                    new_turn = self._new_turn(len(turns), decision, next_question, language, self._stamp())
                    turns.append(new_turn)
                    changed.append(new_turn)
            if decision.action == Action.END or len(turns) >= MAX_TURNS and turns[-1] is turn:
                self._finish(row, state, ended_early=False)
            row["turn_count"] = len(turns)

            # 5. persist everything in one transaction, with the profile continuing through the interview
            states = {question.primary_skill: state.skill_state[question.primary_skill]}
            await self._persist(user_id, row, changed, state=state, metrics=[metrics], usage_rows=usage_rows,
                                profile=(profile, states), seniority=row["seniority"])
            return (self._turn_view(turn, language, revealed=row["status"] == "completed"), self._view(stored, state))

    async def hint(self, user_id: uuid.UUID, session_id: uuid.UUID) -> tuple[HintView | None, InterviewView]:
        async with self._lock(session_id):
            stored, plan, state, engine, _ = await self._load(user_id, session_id)
            row, turns, language = stored.row, stored.turns, stored.row["config"]["language"]
            if row["status"] != "in_progress" or not self.config.allow_hints:
                return None, self._view(stored, state)
            turn = turns[-1]
            meta = turn["question_generation_meta"]
            if meta.get("status") != "open":
                return None, self._view(stored, state)
            question = self.catalog.questions[turn["question_key"]]
            level = meta.get("hint_level", 0) + 1
            text = generator.bank_hint(question, level, language)
            if text is None or engine.request_hint() is None:
                return None, self._view(stored, state)
            meta["hint_level"] = level
            meta.setdefault("hints", []).append({"level": level, "text": text})
            row["hints_used"] = row.get("hints_used", 0) + 1
            row["hints_requested_by_user"] = row.get("hints_requested_by_user", 0) + 1
            await self._persist(user_id, row, [turn], state=state)
            return HintView(level=level, text=text), self._view(stored, state)

    async def end(self, user_id: uuid.UUID, session_id: uuid.UUID) -> InterviewView:
        async with self._lock(session_id):
            stored, plan, state, engine, _ = await self._load(user_id, session_id)
            row = stored.row
            if row["status"] == "in_progress":
                open_turn = stored.turns[-1] if stored.turns else None
                if open_turn is not None and open_turn["question_generation_meta"].get("status") in ("open", "failed"):
                    open_turn["question_generation_meta"]["status"] = "skipped"
                    open_turn["question_generation_meta"]["action_after"] = Action.END.value
                self._finish(row, state, ended_early=True)
                await self._persist(user_id, row, [open_turn] if open_turn else [], state=state)
            return self._view(stored, state)

    async def report(self, user_id: uuid.UUID, session_id: uuid.UUID, *, narrative: bool = True) -> InterviewReportView:
        """The report; `narrative=False` returns the plain (template) narrative without waiting for the model."""
        if not narrative:
            stored, plan, state, _, _ = await self._load(user_id, session_id)
            if stored.row["status"] != "completed":
                raise ApiError("conflict", "the report is available once the interview is over")
            return self._report_view(stored, self._report_data(state, plan, stored.row))
        async with self._lock(session_id):
            stored, plan, state, engine, _ = await self._load(user_id, session_id)
            row, language = stored.row, stored.row["config"]["language"]
            if row["status"] != "completed":
                raise ApiError("conflict", "the report is available once the interview is over")
            data = self._report_data(state, plan, row)
            wrapper = row["state"]
            if wrapper.get("narrative") is None and self.config.narrative:
                labels = self.catalog.skill_labels()
                text, source = await reporter.narrative(self.provider if self.config.narrative else None, data,
                                                        language=language, labels=labels, glossary=self.catalog.glossary)
                wrapper["narrative"], wrapper["narrative_source"] = text, source
                await self._persist(user_id, row, [])
            return self._report_view(stored, data)

    # ------------------------------------------------------------------ building blocks

    def _language(self, language: str | None) -> str:
        language = language or self.config.default_language
        if language not in LANGUAGES:
            raise ApiError("validation", f"language must be one of {', '.join(LANGUAGES)}")
        return language

    def _lock(self, session_id: uuid.UUID) -> asyncio.Lock:
        return self._locks.setdefault(session_id, asyncio.Lock())

    def _plan(self, seniority: str, duration_min: int) -> tuple[list[PlanSkill], int, int]:
        key = (seniority, duration_min)
        if key not in self._plans:
            role = self.catalog.roles[self.config.role]
            company = self.catalog.companies[self.config.company]
            if seniority not in role.seniority_profiles:
                seniority = next(iter(role.seniority_profiles))
            profile = role.seniority_profiles[seniority]
            plan = merge_skill_sets(role_rows=role.skill_set, company_rows=company.skill_set, focus_skill_keys=[],
                                    company_weight_share=company.company_weight_share, seniority=seniority,
                                    planned_duration_min=duration_min, catalog=self.catalog.leaf_skills)
            ceiling = getattr(profile, "difficulty_ceiling", 5)
            baseline = getattr(profile, "baseline_difficulty", None) or 2
            self._plans[key] = (plan, ceiling, min(baseline, ceiling))
        plan, ceiling, baseline = self._plans[key]
        return [p.model_copy(deep=True) for p in plan], ceiling, baseline

    def _pool(self, servable) -> list[BankQuestion]:
        """The questions this interview may ask: reviewed and published, unless configured for development."""
        keep = [s for s in servable if s.reviewed or not self.config.reviewed_only]
        for s in keep:
            self._question_ids[s.key] = s.id            # the database id the turn row points at
        return [self.catalog.questions[s.key] for s in keep if s.key in self.catalog.questions]

    async def _pool_for(self, language: str) -> list[BankQuestion]:
        async with self.store.transaction() as tx:
            servable = await tx.list_questions(language=language)
        return self._pool(servable)

    def _covered(self, plan: list[PlanSkill], pool: list[BankQuestion], language: str) -> list[PlanSkill]:
        """Drop questioned skills the bank cannot ask about; refuse when nothing is left to ask."""
        coverage = bank.coverage_by_skill(pool, language=language, allow_in_review=not self.config.reviewed_only,
                                          require_parity=self.config.reviewed_only)
        kept = [s for s in plan if s.assessment_mode != AssessmentMode.QUESTIONED or s.key in coverage]
        if not any(s.assessment_mode == AssessmentMode.QUESTIONED for s in kept):
            raise ApiError("no_reviewed_questions",
                           "no reviewed question exists yet for the skills of this role; publish questions first")
        return kept

    @staticmethod
    def _continue_histories(state: SessionState, profile: LoadedProfile) -> None:
        """Start each session skill from the candidate's profile state, keeping its history and turn count;
        only the session-local controller fields are reset."""
        for key, fresh in state.skill_state.items():
            known = profile.states.get(key)
            if known is None:
                continue
            carried = known.model_copy(deep=True)
            carried.status, carried.budget, carried.current_difficulty = SkillStatus.UNTOUCHED, fresh.budget, None
            carried.hint_level, carried.partial_count, carried.resolved_reason = 0, 0, None
            carried.core_misconception, carried.level3_hint_difficulty = False, None
            if carried.k is None or carried.c is None:
                carried.k, carried.c = fresh.k, fresh.c
            state.skill_state[key] = carried

    def _engine(self, plan: list[PlanSkill], state: SessionState) -> SessionEngine:
        minimums = {k: s.min_difficulty for k, s in self.catalog.leaf_skills.items()}
        return SessionEngine(plan, state, catalog_min_difficulty=minimums)

    def _select(self, pool: list[BankQuestion], decision: Decision, seen: set[str], language: str,
                fallback_difficulty: int) -> BankQuestion | None:
        difficulty = decision.target_difficulty or fallback_difficulty
        allow_in_review, parity = not self.config.reviewed_only, self.config.reviewed_only
        # never the same question twice in one interview: a skill whose questions are all used up is skipped
        for seen_keys, window, archetype in ((seen, 2, decision.target_archetype), (seen, 9, None)):
            for mode in ("simulation", "deep", "quick"):
                selection = bank.select_question(pool, skill=decision.target_skill, difficulty=difficulty, mode=mode,
                                                 language=language, seen_keys=seen_keys, archetype=archetype,
                                                 allow_in_review=allow_in_review, require_parity=parity,
                                                 difficulty_window=window)
                if selection is not None:
                    return selection.question
        return None

    def _open(self, engine: SessionEngine, plan: list[PlanSkill], state: SessionState, decision: Decision,
              pool: list[BankQuestion], *, seen: set[str], language: str) -> tuple[Decision, BankQuestion | None]:
        """Find a bank question for the decision; a skill the bank cannot ask about is resolved and skipped."""
        for _ in range(len(plan) + 2):
            if decision.action == Action.END or decision.target_skill is None:
                return decision, None
            question = self._select(pool, decision, seen, language, state.current_difficulty or state.baseline_difficulty)
            if question is not None:
                return decision, question
            skill_state = state.skill_state.get(decision.target_skill)
            if skill_state is not None:
                skill_state.status = SkillStatus.BASELINE_MAPPED
                skill_state.resolved_reason = "no_bank_question"
            result = ControllerResult(action=None, reason_code="no_bank_question", resolved=True)
            decision = subject_router.route(state, plan, result, params=engine.params)
        return Decision(action=Action.END, reason_code="no_bank_question"), None

    def _new_turn(self, index: int, decision: Decision, question: BankQuestion, language: str, now: str) -> dict:
        state_difficulty = decision.target_difficulty or question.difficulty
        return {
            "turn_index": index, "skill_key": decision.target_skill or question.primary_skill,
            "question_key": question.key, "question_id": self._question_ids.get(question.key),
            "question_archetype": question.archetype.value, "difficulty": state_difficulty,
            "question_text": question.prompt_with_code(language), "expected_answer_outline": None,
            "question_generation_meta": {"source": "bank", "question_key": question.key, "status": "open",
                                         "hint_level": 0, "hints": [], "decision": decision.action.value,
                                         "reason_code": decision.reason_code, "subject_switch": decision.subject_switch},
            "answer_text": None, "answer_code": None, "answer_language": None, "check_result": None,
            "answer_started_at": now, "answer_submitted_at": None, "asked_at": now, "created_at": now,
        }

    def _finish(self, row: dict, state: SessionState, *, ended_early: bool) -> None:
        row["status"] = "completed"
        row["ended_at"] = self._stamp()
        row["state"]["ended_early"] = ended_early
        row["state"]["engine"] = state.model_dump(mode="json")

    async def _load(self, user_id: uuid.UUID, session_id: uuid.UUID
                    ) -> tuple[StoredSession, list[PlanSkill], SessionState, SessionEngine, LoadedProfile]:
        async with self.store.transaction() as tx:
            stored = await tx.load_session(session_id, user_id=user_id)
            if stored is None:
                raise ApiError("not_found", "interview not found")
            profile = await tx.load_profile(user_id)
        plan = [PlanSkill.model_validate(p) for p in stored.row["config"]["plan"]]
        state = SessionState.model_validate(stored.row["state"]["engine"])
        for turn in stored.turns:
            turn.setdefault("asked_at", turn.get("answer_started_at") or turn.get("created_at"))
            turn.setdefault("question_generation_meta", {})
        return stored, plan, state, self._engine(plan, state), profile

    async def _persist(self, user_id: uuid.UUID, row: dict, turns: list[dict], *, state: SessionState | None = None,
                       metrics: list[dict] | None = None, usage_rows: list[dict] | None = None,
                       profile: tuple[LoadedProfile, dict[str, SkillState]] | None = None,
                       seniority: str | None = None) -> None:
        if state is not None:                      # the engine mutates the live state; the row must carry the latest
            row["state"]["engine"] = state.model_dump(mode="json")
        session_id = uuid.UUID(row["id"])
        async with self.store.transaction() as tx:
            if profile is not None:
                loaded, states = profile
                try:
                    await tx.save_profile(loaded, states)
                except StaleProfile:
                    row["state"].setdefault("flags", []).append("profile_not_updated_stale")
            await tx.save_session(user_id=user_id, row=row, turns=turns, plan=None,
                                  role_slug=self.config.role, company_slug=self.config.company)
            if metrics:
                await tx.record_session_metrics(user_id=user_id, session_id=session_id, metrics=metrics, seniority=seniority,
                                                role_slug=self.config.role, company_slug=self.config.company)
            if usage_rows:
                await tx.record_session_usage(user_id=user_id, session_id=session_id, usage_rows=usage_rows)

    # ------------------------------------------------------------------ report

    def _report_data(self, state: SessionState, plan: list[PlanSkill], row: dict) -> ReportData:
        wrapper = row["state"]
        return reporter.build_report(state, plan, wrapper.get("metrics", []), notes=wrapper.get("notes") or None,
                                     tips_library=list(self.catalog.tips.values()))

    def _report_view(self, stored: StoredSession, data: ReportData) -> InterviewReportView:
        row, language = stored.row, stored.row["config"]["language"]
        labels = self.catalog.skill_labels()

        def labelled(keys: list[str]) -> list[LabelledSkill]:
            return [LabelledSkill(key=k, label=labels.get(k, k)) for k in keys]

        tips_text = []
        for key in data.top_tips:
            tip = self.catalog.tips.get(key)
            if tip is not None:
                template = tip.templates.get(language) or tip.templates.get("en") or ""
                tips_text.append(_PLACEHOLDER.sub("…", template).strip())
        return InterviewReportView(
            session_id=row["id"], language=language, duration_min=row["config"]["duration_min"], turn_count=row["turn_count"],
            fit={scope: FitView(**{k: v for k, v in card.__dict__.items()}) for scope, card in data.scorecards.items()},
            skills=[SkillReportView(key=a.key, label=labels.get(a.key, a.key), subject=a.subject, status=a.status,
                                    proficiency_level=a.proficiency_level, required_level=a.required_level,
                                    level_gap=a.level_gap, turns_count=a.turns_count, hints_used=a.hints_used,
                                    importance=a.importance, strengths=a.strengths, gaps=a.gaps) for a in data.assessments],
            subjects=[{**s, "label": labels.get(s["key"], s["key"])} for s in data.subjects],
            timeline=data.timeline, recommended_next_skills=labelled(data.recommended_next_skills),
            cover_next_time=labelled(data.cover_next_time), top_tips=tips_text,
            narrative_md=row["state"].get("narrative") or reporter.fallback_narrative(data, labels, language),
            narrative_source=row["state"].get("narrative_source") or "fallback",
            turns=[self._turn_view(t, language, revealed=True) for t in stored.turns
                   if t["question_generation_meta"].get("status") in ("done", "failed", "skipped")])

    # ------------------------------------------------------------------ views

    def _turn_view(self, turn: dict, language: str, *, revealed: bool) -> InterviewTurnView:
        meta = turn.get("question_generation_meta") or {}
        skill = turn["skill_key"]
        catalog_skill = self.catalog.skills.get(skill)
        check = turn.get("check_result")
        return InterviewTurnView(
            index=turn["turn_index"], skill=skill, skill_label=catalog_skill.label if catalog_skill else skill,
            subject=(catalog_skill.subject if catalog_skill else None) or "", difficulty=turn["difficulty"],
            archetype=turn["question_archetype"], question=turn["question_text"], question_key=turn.get("question_key"),
            status=meta.get("status", "open"), hints=[HintView(**h) for h in meta.get("hints", [])],
            answer=turn.get("answer_text"), asked_at=turn.get("asked_at") or turn.get("created_at"),
            answered_at=turn.get("answer_submitted_at"),
            band=meta.get("band") if revealed else None, summary=meta.get("summary") if revealed else None,
            key_points_hit=meta.get("key_points_hit", []) if revealed else [],
            key_points_missed=meta.get("key_points_missed", []) if revealed else [],
            check=CheckView(type=check.get("type", ""), passed=check.get("passed"), detail=check.get("detail", ""),
                            mismatches=list(check.get("mismatches") or [])[:8]) if revealed and check else None,
            action_after=meta.get("action_after") if revealed else None,
            subject_switch=bool(meta.get("subject_switch", False)))

    def _view(self, stored: StoredSession, state: SessionState) -> InterviewView:
        row, turns, language = stored.row, stored.turns, stored.row["config"]["language"]
        completed = row["status"] == "completed"
        open_turn = next((t for t in reversed(turns) if t["question_generation_meta"].get("status") in ("open", "evaluating", "failed")), None)
        if completed:
            open_turn = None
        done = [t for t in turns if t is not open_turn and t["question_generation_meta"].get("status") in ("done", "skipped")]
        status = row["status"]
        if status == "in_progress" and open_turn is not None and open_turn["question_generation_meta"].get("status") == "evaluating":
            status = "evaluating"
        labels = self.catalog.skill_labels()
        plan = [InterviewPlanSkill(skill=p["key"], label=labels.get(p["key"], p["key"]), subject=p["subject"],
                                   importance=p["importance"], required_level=p["required_level"],
                                   planned_turns=p.get("planned_turns", 0))
                for p in row["config"]["plan"] if p.get("assessment_mode") == "questioned"]
        can_hint = False
        if open_turn is not None and self.config.allow_hints and open_turn["question_generation_meta"].get("status") == "open":
            skill_state = state.skill_state.get(open_turn["skill_key"])
            question = self.catalog.questions.get(open_turn["question_key"])
            level = open_turn["question_generation_meta"].get("hint_level", 0) + 1
            can_hint = bool(skill_state and skill_state.budget > 0 and question
                            and generator.bank_hint(question, level, language) is not None)
        return InterviewView(
            id=row["id"], status=status, language=language, duration_min=row["config"]["duration_min"],
            elapsed_ms=state.elapsed_ms, remaining_min=round(state.remaining_min, 1), started_at=row["started_at"],
            ended_at=row.get("ended_at"), ended_early=bool(row["state"].get("ended_early")), turn_count=len(turns),
            current_turn=self._turn_view(open_turn, language, revealed=False) if open_turn else None,
            turns=[self._turn_view(t, language, revealed=completed) for t in done], plan=plan,
            can_answer=open_turn is not None and open_turn["question_generation_meta"].get("status") in ("open", "failed"),
            can_hint=can_hint, hints_used=row.get("hints_used", 0), results_revealed=completed, report_ready=completed)


def _now() -> str:
    return datetime.now(UTC).isoformat()


__all__ = ["InterviewConfig", "InterviewService", "DURATIONS", "MAX_TURNS", "copy"]
