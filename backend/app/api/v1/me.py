"""The signed-in user: identity, pilot access, professional-skill progress."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.deps import CurrentAccess, Practice
from app.schemas.api import GoalView, ProgressView

router = APIRouter(prefix="/v1/me", tags=["me"])


class Me(BaseModel):
    id: str
    email: str | None
    pilot_member: bool
    can_manage_tasks: bool


@router.get("", response_model=Me, summary="Who am I, as the backend sees me")
async def me(access: CurrentAccess) -> Me:
    return Me(id=str(access.user_id), email=access.email, pilot_member=access.is_member,
              can_manage_tasks=access.can_manage_tasks)


@router.get("/progress", response_model=ProgressView,
            summary="Progress: overview card, timeline, the plan until the interview, skills and subjects")
async def progress(access: CurrentAccess, practice: Practice,
                   language: str | None = Query(None, pattern="^(en|he)$")) -> ProgressView:
    return await practice.progress(access.user_id, language=language)


class GoalRequest(BaseModel):
    job_type: str | None = Field(None, max_length=40, description="a key from GET /v1/job-types")
    interview_date: date | None = None
    minutes_per_day: int | None = Field(None, ge=1, le=1440)
    seniority: str | None = Field(None, max_length=20)
    language: str | None = Field(None, pattern="^(en|he)$")


@router.get("/goal", response_model=GoalView, summary="What I am preparing for (job type, interview date, minutes a day)")
async def get_goal(access: CurrentAccess, practice: Practice,
                   language: str | None = Query(None, pattern="^(en|he)$")) -> GoalView:
    return await practice.get_goal(access.user_id, language=language)


@router.post("/goal", response_model=GoalView, summary="Set or change my goal")
async def save_goal(body: GoalRequest, access: CurrentAccess, practice: Practice) -> GoalView:
    return await practice.save_goal(access.user_id, job_type=body.job_type, interview_date=body.interview_date,
                                    minutes_per_day=body.minutes_per_day, seniority=body.seniority, language=body.language)
