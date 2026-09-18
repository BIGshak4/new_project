"""Request-scoped dependencies: the verified user and their pilot access."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app import db
from app.api.errors import ApiError
from app.auth import AuthenticatedUser, current_user
from app.config import get_settings
from app.repo.users import Access, resolve_access


async def _db_access(user: AuthenticatedUser) -> Access:
    async with db.get_engine().begin() as connection:
        return await resolve_access(connection, user)


async def current_access(request: Request, user: Annotated[AuthenticatedUser, Depends(current_user)]) -> Access:
    """The caller's access record. Tests replace `app.state.access_resolver`; production hits the database."""
    resolver = getattr(request.app.state, "access_resolver", None) or _db_access
    access: Access = await resolver(user)
    if get_settings().require_pilot_membership and not access.is_member:
        raise ApiError("forbidden", "this account is not on the pilot list yet")
    return access
