"""The authenticated daily puzzle and its separately revealed reference solution."""

from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from app.api.deps import CurrentAccess
from app.api.errors import ApiError
from app.services.daily_puzzle import DailyPuzzleService

router = APIRouter(prefix="/v1/games/daily-puzzle", tags=["daily puzzle"])
Language = Literal["he", "en"]


class PuzzleView(BaseModel):
    day: date
    expires_at: datetime
    id: str
    title: str
    prompt: str
    subject: str


class RevealRequest(BaseModel):
    day: date
    id: str = Field(min_length=1, max_length=160)


class SolutionView(BaseModel):
    day: date
    id: str
    solution: str


def daily_service(request: Request) -> DailyPuzzleService:
    runtime = getattr(request.app.state, "runtime", None)
    if runtime is None or runtime.daily_puzzle is None:
        raise ApiError("temporarily_unavailable", "Daily puzzles are not started.")
    return runtime.daily_puzzle


DailyService = Annotated[DailyPuzzleService, Depends(daily_service)]


@router.get("", response_model=PuzzleView)
async def current_puzzle(access: CurrentAccess, service: DailyService, response: Response, language: Language = "he"):
    response.headers["Cache-Control"] = "private, no-store"
    return service.today(language)


@router.post("/reveal", response_model=SolutionView)
async def reveal_solution(body: RevealRequest, access: CurrentAccess, service: DailyService, response: Response,
                          language: Language = "he"):
    response.headers["Cache-Control"] = "private, no-store"
    return service.reveal(body.day, body.id, language)
