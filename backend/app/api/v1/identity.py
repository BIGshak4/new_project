"""Own permanent identity, a bounded public name check, and explicit friendship requests."""

import time
import uuid
from collections import OrderedDict, deque
from typing import Literal

from fastapi import APIRouter, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import CurrentAccess, Identities
from app.api.errors import ApiError
from app.api.v1.avatars import AvatarConfig

router = APIRouter(tags=["identity and friends"])


class IdentityView(BaseModel):
    username: str | None
    friend_code: str
    can_claim_username: bool


class UsernameClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(..., min_length=1, max_length=96)


class UsernameAvailability(BaseModel):
    available: bool
    reason: Literal["invalid", "offensive", "taken"] | None


class FriendPerson(BaseModel):
    user_id: str
    username: str | None
    friend_code: str
    avatar: AvatarConfig | None


class FriendRequestView(BaseModel):
    id: str
    person: FriendPerson
    created_at: str


class FriendsView(BaseModel):
    friends: list[FriendPerson]
    incoming: list[FriendRequestView]
    outgoing: list[FriendRequestView]


class FriendRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    friend_code: str = Field(..., min_length=1, max_length=24)


class SocialBudget:
    def __init__(self):
        self.buckets: OrderedDict[tuple[str, str], deque[float]] = OrderedDict()

    def check(self, scope, key, maximum):
        now = time.monotonic()
        bucket = self.buckets.setdefault((scope, key), deque())
        self.buckets.move_to_end((scope, key))
        while bucket and bucket[0] <= now - 60:
            bucket.popleft()
        if len(bucket) >= maximum:
            raise ApiError("usage_limit", "please wait before trying again", status=429, headers={"Retry-After": "60"})
        bucket.append(now)
        while len(self.buckets) > 3000:
            self.buckets.popitem(last=False)


budget = SocialBudget()


def _limit(request: Request, scope: str, maximum: int, user_id=None):
    # Only the server-resolved peer is trusted. Caller-supplied forwarding headers cannot reset this budget.
    address = request.client.host if request.client else "unknown"
    budget.check(scope, f"ip:{address}", maximum)
    if user_id is not None:
        budget.check(scope, f"user:{user_id}", maximum)


@router.get("/v1/usernames/availability", response_model=UsernameAvailability,
            summary="Check a candidate username without returning account details")
async def username_availability(request: Request, response: Response, identities: Identities,
                                username: str = Query(..., max_length=96)):
    _limit(request, "username-check", 30)
    response.headers["Cache-Control"] = "no-store"
    return await identities.availability(username)


@router.get("/v1/me/identity", response_model=IdentityView)
async def identity(access: CurrentAccess, identities: Identities, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return await identities.get(access.user_id)


@router.put("/v1/me/identity/username", response_model=IdentityView,
            summary="Claim a permanent username once for an existing account")
async def claim_username(body: UsernameClaim, request: Request, access: CurrentAccess, identities: Identities):
    _limit(request, "username-claim", 10, access.user_id)
    return await identities.claim(access.user_id, body.username)


@router.get("/v1/me/friends", response_model=FriendsView)
async def friends(access: CurrentAccess, identities: Identities, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return await identities.friends(access.user_id)


@router.post("/v1/me/friends/requests", response_model=FriendsView)
async def request_friend(body: FriendRequestBody, request: Request, access: CurrentAccess, identities: Identities):
    _limit(request, "friend-request", 20, access.user_id)
    return await identities.request(access.user_id, body.friend_code)


@router.post("/v1/me/friends/requests/{request_id}/accept", response_model=FriendsView)
async def accept_friend(request_id: uuid.UUID, access: CurrentAccess, identities: Identities):
    return await identities.accept(access.user_id, request_id)


@router.post("/v1/me/friends/requests/{request_id}/decline", response_model=FriendsView)
async def decline_friend(request_id: uuid.UUID, access: CurrentAccess, identities: Identities):
    return await identities.dismiss(access.user_id, request_id, incoming=True)


@router.delete("/v1/me/friends/requests/{request_id}", response_model=FriendsView)
async def cancel_friend_request(request_id: uuid.UUID, access: CurrentAccess, identities: Identities):
    return await identities.dismiss(access.user_id, request_id, incoming=False)


@router.delete("/v1/me/friends/{user_id}", response_model=FriendsView)
async def remove_friend(user_id: uuid.UUID, access: CurrentAccess, identities: Identities):
    return await identities.remove(access.user_id, user_id)
