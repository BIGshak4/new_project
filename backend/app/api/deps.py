"""Request-scoped dependencies: the verified user, their pilot access, the practice service."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app import db
from app.api.errors import ApiError
from app.auth import AuthenticatedUser, current_user
from app.config import get_settings
from app.repo import cache
from app.repo.users import Access, resolve_access
from app.services.avatars import AvatarsService
from app.services.billing import BillingService
from app.services.coins import CoinsService
from app.services.duels import DuelService
from app.services.interview_service import InterviewService
from app.services.practice_service import PracticeService


async def _db_access(user: AuthenticatedUser) -> Access:
    async def load() -> Access:
        async with db.get_engine().begin() as connection:
            return await resolve_access(connection, user)
    return await cache.ACCESS.get((user.id, user.email), load)


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


async def paid_access(request: Request, access: Annotated[Access, Depends(current_access)]) -> Access:
    """The access record of a caller who may practise under the payment rule. While REQUIRE_PAYMENT is off (Shaked,
    2026-10-20: not mandatory for now) this is every member; on, an unpaid member gets 402 `payment_required` and
    the billing routes stay open to them."""
    runtime = getattr(request.app.state, "runtime", None)
    billing = getattr(runtime, "billing", None)
    if billing is not None and not await billing.is_entitled(access.user_id):
        raise ApiError("payment_required", "this account has no active plan; choose one on the payment page", status=402)
    return access


def billing_service(request: Request) -> BillingService:
    runtime = getattr(request.app.state, "runtime", None)
    if runtime is None or getattr(runtime, "billing", None) is None:
        raise ApiError("evaluation_unavailable", "billing is not started", status=503)
    return runtime.billing


def coins_service(request: Request) -> CoinsService:
    runtime = getattr(request.app.state, "runtime", None)
    if runtime is None or getattr(runtime, "coins", None) is None:
        raise ApiError("evaluation_unavailable", "coins are not started", status=503)
    return runtime.coins


def duel_service(request: Request) -> DuelService:
    runtime = getattr(request.app.state, "runtime", None)
    if runtime is None or getattr(runtime, "duels", None) is None:
        raise ApiError("evaluation_unavailable", "duels are not started", status=503)
    return runtime.duels


def avatars_service(request: Request) -> AvatarsService:
    runtime = getattr(request.app.state, "runtime", None)
    if runtime is None or getattr(runtime, "avatars", None) is None:
        raise ApiError("evaluation_unavailable", "avatar service is not started", status=503)
    return runtime.avatars


def practice_service(request: Request) -> PracticeService:
    runtime = getattr(request.app.state, "runtime", None)
    if runtime is None:
        raise ApiError("evaluation_unavailable", "the practice service is not started", status=503)
    return runtime.practice


def interview_service(request: Request) -> InterviewService:
    runtime = getattr(request.app.state, "runtime", None)
    if runtime is None or getattr(runtime, "interview", None) is None:
        raise ApiError("evaluation_unavailable", "the interview service is not started", status=503)
    return runtime.interview


CurrentAccess = Annotated[Access, Depends(current_access)]
PaidAccess = Annotated[Access, Depends(paid_access)]
Billing = Annotated[BillingService, Depends(billing_service)]
Coins = Annotated[CoinsService, Depends(coins_service)]
Avatars = Annotated[AvatarsService, Depends(avatars_service)]
Duels = Annotated[DuelService, Depends(duel_service)]
Practice = Annotated[PracticeService, Depends(practice_service)]
Interview = Annotated[InterviewService, Depends(interview_service)]
