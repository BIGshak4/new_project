"""One shared daily prompt, a private graded attempt and the solution after feedback."""
import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from app.api.deps import CurrentAccess, PaidAccess
from app.api.errors import ApiError
from app.api.v1.practice import AnswerBody
from app.schemas.api import SubmissionView
from app.services.daily_puzzle_grading import DailyPuzzleGrading

router = APIRouter(prefix="/v1/games/daily-puzzle", tags=["daily puzzle"])
Language = Literal["he", "en"]


class PuzzleView(BaseModel):
    day: date
    expires_at: datetime
    id: str
    title: str
    prompt: str
    subject: str
    attempt_id: uuid.UUID
    status: Literal["open", "evaluating", "failed", "done"]
    submission: SubmissionView | None
    score: float | None
    passed: bool | None
    feedback_limit: int
    feedback_remaining: int


class PuzzleRequest(BaseModel):
    day: date
    id: str = Field(min_length=1, max_length=160)


class DailyAnswer(PuzzleRequest):
    answer: AnswerBody


class SolutionView(BaseModel):
    day: date
    id: str
    solution: str


def daily_service(request: Request, response: Response) -> DailyPuzzleGrading:
    runtime = getattr(request.app.state, "runtime", None)
    if runtime is None or runtime.daily_grading is None:
        raise ApiError("temporarily_unavailable", "Daily puzzles are not started.")
    response.headers["Cache-Control"] = "private, no-store"
    return runtime.daily_grading


DailyService = Annotated[DailyPuzzleGrading, Depends(daily_service)]


@router.get("", response_model=PuzzleView)
async def current_puzzle(access: CurrentAccess, service: DailyService, language: Language = "he",
                         day: date | None = None):
    return await service.view(access.user_id, language, day)


@router.post("/submit", response_model=PuzzleView)
async def submit_answer(body: DailyAnswer, access: PaidAccess, service: DailyService, response: Response,
                        language: Language = "he"):
    result = await service.submit(access.user_id, language, body.day, body.id, answer=body.answer)
    response.status_code = 202 if result["status"] == "evaluating" else 200
    return result


@router.post("/retry", response_model=PuzzleView)
async def retry_answer(body: PuzzleRequest, access: PaidAccess, service: DailyService, response: Response,
                       language: Language = "he"):
    result = await service.submit(access.user_id, language, body.day, body.id, retry=True)
    response.status_code = 202 if result["status"] == "evaluating" else 200
    return result


@router.post("/reveal", response_model=SolutionView)
async def reveal_solution(body: PuzzleRequest, access: CurrentAccess, service: DailyService, language: Language = "he"):
    status = await service.view(access.user_id, language, body.day)
    if status["id"] != body.id or status["status"] != "done":
        raise ApiError("conflict", "The solution opens after today's answer has been graded.")
    return {"day": body.day, "id": body.id, "solution": service.calendar.for_day(body.day).solution[language]}
