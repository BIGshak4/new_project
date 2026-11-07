"""The signed-in user: identity, pilot access, professional-skill progress."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, Query, Request
from pydantic import BaseModel, Field

from app.api.deps import CurrentAccess, Practice
from app.schemas.api import GoalView, ProgramStartView, ProgramView, ProgressView, ReadinessView
from app.services.coins import CoinsService

router = APIRouter(prefix="/v1/me", tags=["me"])


def _coins_if_started(request: Request) -> CoinsService | None:
    """Who-am-I must answer even on a server where coins are not started (tests, a bare runtime): then no balance."""
    runtime = getattr(request.app.state, "runtime", None)
    return getattr(runtime, "coins", None) if runtime is not None else None


CoinsIfStarted = Annotated[CoinsService | None, Depends(_coins_if_started)]


class Me(BaseModel):
    id: str
    email: str | None
    pilot_member: bool
    can_manage_tasks: bool
    coins: int | None = None                    # the balance, for the header of every screen (Shaked, 2026-11-06); None: coins off


@router.get("", response_model=Me, summary="Who am I, as the backend sees me, and my coin balance")
async def me(access: CurrentAccess, coins: CoinsIfStarted) -> Me:
    return Me(id=str(access.user_id), email=access.email, pilot_member=access.is_member,
              can_manage_tasks=access.can_manage_tasks,
              coins=await coins.balance(access.user_id) if coins is not None else None)


@router.get("/progress", response_model=ProgressView,
            summary="Progress: overview card, timeline, the plan until the interview, skills and subjects")
async def progress(access: CurrentAccess, practice: Practice,
                   language: str | None = Query(None, pattern="^(en|he)$")) -> ProgressView:
    return await practice.progress(access.user_id, language=language)


class ActivityDayView(BaseModel):
    date: str
    questions: int


class ActivityView(BaseModel):
    timezone: str
    today: str
    streak_days: int
    today_count: int
    last_solved_date: str | None
    days: list[ActivityDayView]


@router.get("/activity", response_model=ActivityView, summary="My solved-question days and current streak")
async def activity(access: CurrentAccess, practice: Practice,
                   timezone: str = Query("UTC", min_length=1, max_length=100)) -> ActivityView:
    return ActivityView(**await practice.activity(access.user_id, timezone=timezone))


class GoalRequest(BaseModel):
    job_type: str | None = Field(None, max_length=40, description="a key from GET /v1/job-types")
    job_types: list[Annotated[str, Field(min_length=1, max_length=40)]] | None = Field(None, max_length=30)
    learning_mode: Literal["targeted", "explore"] = "targeted"
    interview_date: date | None = None
    minutes_per_day: int | None = Field(None, ge=5, le=600, strict=True)
    seniority: str | None = Field(None, max_length=20)
    language: str | None = Field(None, pattern="^(en|he)$")


@router.get("/goal", response_model=GoalView, summary="What I am preparing for (job type, interview date, minutes a day)")
async def get_goal(access: CurrentAccess, practice: Practice,
                   language: str | None = Query(None, pattern="^(en|he)$")) -> GoalView:
    return await practice.get_goal(access.user_id, language=language)


@router.get("/readiness", response_model=ReadinessView,
            summary="How ready I am for the job type in my goal: its skills, where I stand on each, and what to practise next",
            description="`skills` are the job type's skills, heaviest first, each with the required level, the user's level, "
                        "the gap and how fresh the evidence is. `readiness_word` (and the score behind it) is given only when "
                        "`ready_to_judge` is true, which needs counted evidence on 60 % of the job type's weight; until then "
                        "`next_questions` says what to answer first. A change of job type in the goal rebuilds the plan at once.")
async def readiness(access: CurrentAccess, practice: Practice,
                    language: str | None = Query(None, pattern="^(en|he)$")) -> ReadinessView:
    return await practice.readiness(access.user_id, language=language)


@router.post("/goal", response_model=GoalView, summary="Set or change my goal")
async def save_goal(body: GoalRequest, access: CurrentAccess, practice: Practice) -> GoalView:
    return await practice.save_goal(access.user_id, job_type=body.job_type, interview_date=body.interview_date,
                                    minutes_per_day=body.minutes_per_day, seniority=body.seniority, language=body.language,
                                    job_types=body.job_types, learning_mode=body.learning_mode)


class ProgramStartRequest(BaseModel):
    item_id: uuid.UUID | None = Field(None, description="a plan item from GET /v1/me/program; the next due one when "
                                                        "omitted, or the 'ahead' one once today's items are done. An item "
                                                        "of a later day opens only once today's items are done")
    language: str | None = Field(None, pattern="^(en|he)$")


@router.get("/program", response_model=ProgramView,
            summary="My program: the saved plan rolled to today, what is due now, the item to start",
            description="`next` is today's item to start. Once today's items are all done, `ahead` is the first open "
                        "item of the following days, which POST /v1/me/program/start opens.")
async def program(access: CurrentAccess, practice: Practice,
                  language: str | None = Query(None, pattern="^(en|he)$")) -> ProgramView:
    return await practice.program(access.user_id, language=language)


@router.post("/program/start", response_model=ProgramStartView,
             summary="Start a program item: opens a practice attempt on a fitting question, or points to the interview lobby")
async def start_program(body: ProgramStartRequest, access: CurrentAccess, practice: Practice,
                        user_agent: Annotated[str | None, Header()] = None) -> ProgramStartView:
    from app.api.v1.practice import device_of
    return await practice.start_program_item(access.user_id, item_id=body.item_id, language=body.language,
                                             device=device_of(user_agent))
