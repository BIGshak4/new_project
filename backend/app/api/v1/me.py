from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import current_access
from app.repo.users import Access

router = APIRouter(prefix="/v1/me", tags=["me"])


class Me(BaseModel):
    id: str
    email: str | None
    pilot_member: bool
    can_manage_tasks: bool


@router.get("", response_model=Me, summary="Who am I, as the backend sees me")
async def me(access: Annotated[Access, Depends(current_access)]) -> Me:
    return Me(id=str(access.user_id), email=access.email, pilot_member=access.is_member,
              can_manage_tasks=access.can_manage_tasks)
