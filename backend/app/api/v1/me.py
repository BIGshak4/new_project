"""The signed-in user: identity, pilot access, professional-skill progress."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentAccess, Practice
from app.schemas.api import ProgressView

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
            summary="Durable skill progress: level, evidence status, trend, recent attempts")
async def progress(access: CurrentAccess, practice: Practice) -> ProgressView:
    return await practice.progress(access.user_id)
