"""Account-bound avatar and cosmetic shop operations. Prices and ownership never come from the caller."""
from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import Avatars, CurrentAccess

router = APIRouter(prefix="/v1/me/avatar", tags=["avatar"])


class AvatarConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    component: str = Field(..., min_length=1, max_length=24)
    color: str = Field(..., min_length=1, max_length=24)
    skin: str = Field(..., min_length=1, max_length=24)


class CosmeticBuy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skin: str = Field(..., min_length=1, max_length=24)


class AvatarView(BaseModel):
    avatar: AvatarConfig
    owned_skins: list[str]
    components: list[dict]
    colors: list[dict]
    skins: list[dict]
    balance: int
    enabled: bool
    shop_enabled: bool
    shirt_text: str = "Job_Run"
    capabilities: dict


@router.get("", response_model=AvatarView, summary="My avatar, owned skins and the server-priced cosmetic catalog")
async def get_avatar(access: CurrentAccess, avatars: Avatars,
                     language: str = Query("he", pattern="^(en|he)$")):
    return await avatars.get(access.user_id)


@router.put("", response_model=AvatarView, summary="Choose a free component/color and an owned skin")
async def save_avatar(body: AvatarConfig, access: CurrentAccess, avatars: Avatars):
    return await avatars.save(access.user_id, body.model_dump())


@router.post("/buy", response_model=AvatarView, summary="Buy a permanent cosmetic skin once with earned coins")
async def buy_skin(body: CosmeticBuy, access: CurrentAccess, avatars: Avatars):
    return await avatars.buy(access.user_id, body.skin)
