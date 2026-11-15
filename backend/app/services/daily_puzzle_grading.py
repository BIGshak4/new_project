"""A daily submission shares the practice judge, feedback cards and monthly allowances.

Model calls run after the first answer and its quota reservation commit.
A database row lock protects the immutable answer across tabs, devices and workers.
"""
import asyncio
import logging
import uuid
from datetime import timedelta
from decimal import Decimal

from app.api.errors import ApiError
from app.engine import evaluator, feedback, scores, visual_evidence
from app.engine.practice import EVALUATION_BUDGET_SECONDS, UsageEvent, assessed_by
from app.schemas.api import CardView, SubmissionView
from app.schemas.bank import BankQuestion, QuestionText, RubricCriterion
from app.services.budget import monthly_budget_left
from app.services.daily_puzzle import DailyPuzzleService
from app.services.daily_puzzle_bank import DailyPuzzleEntry
from app.services.feedback_quota import monthly_feedback_remaining, release_monthly_feedback, reserve_monthly_feedback
from app.services.practice_service import PracticeService

log = logging.getLogger("app.daily_puzzle")


def variant_question(source: BankQuestion, entry: DailyPuzzleEntry, language: str) -> BankQuestion:
    """The judge must see the exact displayed variant, never the source prompt's rubric, code or assumptions."""
    text = QuestionText(title=entry.title[language], prompt=entry.prompt[language], reference_solution=entry.solution[language],
                        requirements={"he": "פתרו את החידה לפי התנאים בנוסח המוצג.",
                                      "en": "Solve the puzzle under the conditions in the displayed prompt."}[language])
    rubric = RubricCriterion(key="solution", weight=1, description={
        "en": "Check the requested result and reasoning against this variant's constraints. Accept other valid solutions.",
        "he": "בדקו את התוצאה ואת ההסבר לפי הדרישות בנוסח הזה. קבלו גם פתרונות נכונים אחרים."})
    return source.model_copy(update=dict(key=entry.id, translations={language: text}, rubric=[rubric], assets={},
                                         common_errors=[], deterministic_check=None, format="explain"))


def mark_failed(row: dict) -> None:
    row.update(status="failed", claimed_at=None, lease_id=None)
    row["submission"] = {**row["submission"], "status": "failed"}


class DailyPuzzleGrading:
    def __init__(self, calendar: DailyPuzzleService, practice: PracticeService):
        self.calendar = calendar
        self.practice = practice
        self.tasks = set()

    async def _load(self, tx, user_id, language, day=None, puzzle_id=None, *, for_update=False):
        today = self.calendar.today(language)
        if day is None or day == today["day"]:
            puzzle = today
            if puzzle_id is not None and puzzle_id != puzzle["id"]:
                raise ApiError("conflict", "This is not today's puzzle.")
            row = await tx.daily_attempt(user_id, puzzle["day"], puzzle["id"], for_update=for_update)
        else:
            # A late-night submission may finish after midnight. Only the owner of a saved
            # answer can read that day's feedback or retry the same saved answer.
            if day > today["day"]:
                raise ApiError("conflict", "This puzzle is not available.")
            row = await tx.daily_attempt(user_id, day, None, for_update=for_update)
            if row is None or row["status"] == "open":
                raise ApiError("conflict", "There is no submitted daily answer for this day.")
            puzzle = self.calendar.puzzle_on(day, language)
        if row["puzzle_key"] != puzzle["id"] or (puzzle_id is not None and puzzle_id != row["puzzle_key"]):
            raise ApiError("conflict", "The saved answer belongs to another puzzle.")
        return puzzle, row

    async def _expire(self, tx, user_id):
        # A stopped worker leaves the answer recoverable. Also clean older days so an abandoned
        # request from yesterday never consumes today's remaining quota on the next daily visit.
        cutoff = self.calendar.clock() - timedelta(seconds=EVALUATION_BUDGET_SECONDS)
        for item in await tx.expired_daily_attempts(user_id, cutoff):
            mark_failed(item)
            await tx.save_daily_attempt(item)
            await release_monthly_feedback(tx, user_id, item["id"])

    async def view(self, user_id, language, day=None):
        limit = self.practice.config.monthly_feedback_limit
        async with self.practice.store.transaction() as tx:
            await self._expire(tx, user_id)
            puzzle, row = await self._load(tx, user_id, language, day)
            remaining = await monthly_feedback_remaining(tx, user_id, limit)
        return self._view(puzzle, row, remaining, limit)

    @staticmethod
    def _view(puzzle, row, remaining, limit):
        score = row["score"]
        return {**puzzle, "attempt_id": row["id"], "status": row["status"], "submission": row["submission"],
                "score": score, "passed": score > 90 if score is not None else None,
                "feedback_limit": limit, "feedback_remaining": remaining}

    async def submit(self, user_id, language, day, puzzle_id, *, answer=None, retry=False):
        limit = self.practice.config.monthly_feedback_limit
        lease = None
        async with self.practice.store.transaction() as tx:
            await self._expire(tx, user_id)
            puzzle, row = await self._load(tx, user_id, language, day, puzzle_id, for_update=True)
            status = row["status"]
            if not retry and status != "open":
                previous = row["submission"]
                if (previous["answer"], previous["visual"]) != (answer.text.strip(), self._visual(answer)):
                    raise ApiError("already_submitted", "Today's answer was already submitted.")
            elif retry and status == "open":
                raise ApiError("nothing_to_retry", "Today's puzzle has no saved answer.")
            elif status == "open" or (retry and status == "failed"):
                if status == "open":
                    visual = self._visual(answer)
                    if not answer.text.strip() and not visual:
                        raise ApiError("validation", "Enter a solution before submitting.")
                    if visual and answer.visual.images and not await tx.validate_answer_images(user_id, row["id"], answer.visual.images):
                        raise ApiError("validation", "An answer image is missing or does not belong to today's puzzle.")
                    row["language"] = language
                    row["submission"] = SubmissionView(revision=1, key=str(row["id"]), turn=0, answer=answer.text.strip(),
                                                       visual=answer.visual if visual else None, status="evaluating",
                                                       accepted_at=self.calendar.clock().isoformat()).model_dump(mode="json")
                await monthly_budget_left(tx, user_id, self.practice.config.monthly_budget_usd)
                await reserve_monthly_feedback(tx, user_id, row["id"], limit)
                lease = uuid.uuid4()
                row.update(status="evaluating", claimed_at=self.calendar.clock(), lease_id=lease)
                row["submission"]["status"] = "evaluating"
                await tx.save_daily_attempt(row)
            remaining = await monthly_feedback_remaining(tx, user_id, limit)
        if lease:
            task = asyncio.create_task(self._grade(row, lease))
            self.tasks.add(task)
            task.add_done_callback(self._finished)
        return self._view(puzzle, row, remaining, limit)

    @staticmethod
    def _visual(answer):
        return answer.visual.model_dump(mode="json") if answer.visual and answer.visual.has_content else None

    def _finished(self, task):
        self.tasks.discard(task)
        if not task.cancelled() and task.exception():
            log.error("Could not persist daily grading: %r", task.exception())

    async def drain(self):
        if self.tasks:
            _, pending = await asyncio.wait(list(self.tasks), timeout=15)
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

    async def _grade(self, row, lease):
        usage = []
        graded = None
        try:
            async with asyncio.timeout(EVALUATION_BUDGET_SECONDS - 30):
                graded = await self._judge(row, usage)
        except asyncio.CancelledError:
            # Persist a recoverable failure on a graceful restart. A hard stop is handled by the lease.
            pass
        except Exception:
            log.exception("Daily puzzle grading failed for attempt %s", row["id"])
        user_id = row["user_id"]
        async with self.practice.store.transaction() as tx:
            current = await tx.daily_attempt(user_id, row["puzzle_day"], row["puzzle_key"], for_update=True)
            if current["lease_id"] != lease:
                return
            if graded:
                current["submission"], current["score"] = graded
                current.update(status="done", lease_id=None, claimed_at=None)
            else:
                mark_failed(current)
                await release_monthly_feedback(tx, user_id, current["id"])
            await tx.save_daily_attempt(current)
            # Daily attempts have their own parent table; bank usage_event.attempt_id references
            # regular attempts, so store the daily scope in metadata and use the same monthly cost ledger.
            for event in usage:
                event["meta"]["daily_puzzle_attempt_id"] = str(current["id"])
            if usage:
                await tx.record_usage(user_id=user_id, attempt_id=None, usage_rows=usage)

    async def _judge(self, row, usage):
        entry = self.calendar.for_day(row["puzzle_day"])
        if entry.id != row["puzzle_key"]:
            raise ValueError("Saved daily puzzle no longer matches the grading reference")
        language = row["language"]
        source = self.practice.catalog.questions[entry.source_question_key]
        question = variant_question(source, entry, language)
        sub = SubmissionView.model_validate(row["submission"])
        visual = await visual_evidence.gather(sub.visual, self.practice.image_fetcher)
        if visual.missing:
            return None  # recoverable; a user's only chance must include every supplied photo
        result = await evaluator.evaluate(self.practice.provider, language=language, difficulty=source.difficulty,
            question_context=evaluator.question_block(question, language, self.practice.catalog.skills.get(source.primary_skill)),
            known_error_keys=set(), answer=sub.answer, glossary=self.practice.catalog.glossary,
            circuit=visual.circuit, images=visual.images)
        if result.model:
            usage.append(UsageEvent("evaluate", result.model, result.usage, result.latency_ms).as_row("deep"))
        if not result.ok or assessed_by(result.model) != "model":
            return None
        evaluation = result.evaluation
        band = scores.classify_band(evaluation)
        card = await feedback.build_card(self.practice.provider, question=question, evaluation=evaluation, band=band,
            answer="\n".join(filter(None, (sub.answer, visual.circuit))), check=None, language=language,
            glossary=self.practice.catalog.glossary)
        if card.model:
            usage.append(UsageEvent("feedback", card.model, card.usage, card.latency_ms).as_row("deep"))
        view = sub.model_copy(update=dict(status="done", evaluated_at=self.calendar.clock().isoformat(), band=band.value,
            summary=evaluation.one_line_summary, key_points_hit=evaluation.key_points_hit,
            key_points_missed=evaluation.key_points_missed, card=CardView.model_validate(card.card.model_dump()), assessed_by=assessed_by(result.model),
            model=result.model, flags=[*result.flags, *visual.flags], related=scores.related_to_question(evaluation, flags=result.flags)))
        score = Decimal(str(evaluation.correctness)) * 100
        return view.model_dump(mode="json"), score
