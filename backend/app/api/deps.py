"""Request-scoped dependencies: the verified user, their pilot access, the practice service."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app import db
from app.api.errors import ApiError
from app.auth import AuthenticatedUser, current_user
from app.config import get_settings
from app.repo.users import Access, resolve_access
from app.services.practice_service import PracticeService


async def _db_access(user: AuthenticatedUser) -> Access:
    async with db.get_engine().begin() as connection:
        return await resolve_access(connection, user)


async def _memory_access(user: AuthenticatedUser) -> Access:
    """No database: every signed-in user is a member (development only)."""
    return Access(user_id=user.id, email=user.email, is_member=True, can_manage_tasks=False, profile_created=False)


async def current_access(request: Request, user: Annotated[AuthenticatedUser, Depends(current_user)]) -> Access:
    """The caller's access record. Tests replace `app.state.access_resolver`; production hits the database."""
    resolver = getattr(request.app.state, "access_resolver", None)
    if resolver is None:
        runtime = getattr(request.app.state, "runtime", None)
        resolver = _db_access if runtime is None or runtime.store_kind == "database" else _memory_access
    access: Access = await resolver(user)
    request.state.user_id = str(access.user_id)
    if get_settings().require_pilot_membership and not access.is_member:
        raise ApiError("forbidden", "this account is not on the pilot list yet")
    return access


def practice_service(request: Request) -> PracticeService:
    runtime = getattr(request.app.state, "runtime", None)
    if runtime is None:
        raise ApiError("evaluation_unavailable", "the practice service is not started", status=503)
    return runtime.practice


CurrentAccess = Annotated[Access, Depends(current_access)]
Practice = Annotated[PracticeService, Depends(practice_service)]
