"""Coins: the wallet, the shop, and what earns coins (Shaked, 2026-10-22).

Coins are earned, never bought, never cashed out: `no_monetary_value` is true on every wallet and the text says so.
XP is unchanged and lives on the progress page; coins are a second number next to it.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.deps import Coins, CurrentAccess, Practice

router = APIRouter(prefix="/v1/me/coins", tags=["coins"])


class CoinMovementView(BaseModel):
    delta: int                                  # positive = received, negative = spent or staked
    kind: str                                   # gift | earn | spend | stake | payout | refund | forfeit
    item: str | None = None                     # the shop item, for a spend
    duel_id: str | None = None
    at: datetime


class ShopItemView(BaseModel):
    key: str
    label: str
    description: str
    price: int
    affordable: bool


class CoinRulesView(BaseModel):
    starting_gift: int
    strong_answer: int                          # coins for a STRONG main answer (within the hint allowance, reference unseen, on topic)
    strong_hard_answer: int                     # ... when the question is at or above `hard_difficulty_from`
    hard_difficulty_from: int
    strong_interview_turn: int
    max_hints_for_coins: int
    duel_stake: int


class WalletView(BaseModel):
    balance: int
    earned_today: int
    extra_questions_today: int                  # what the shop added to today's question limit
    daily_limit: int                            # today's limit including the shop's top-ups
    movements: list[CoinMovementView] = Field(default_factory=list)
    shop: list[ShopItemView] = Field(default_factory=list)
    rules: CoinRulesView
    enabled: bool                               # false until the ledger migration is applied: everything reads 0
    no_monetary_value: bool = True              # coins cannot be bought or cashed out; say so on the screen


class BuyRequest(BaseModel):
    item: str = Field(..., max_length=40)


def _view(wallet, daily_limit: int, language: str) -> WalletView:
    r = wallet.rules
    return WalletView(
        balance=wallet.balance, earned_today=wallet.earned_today, extra_questions_today=wallet.extra_questions_today,
        daily_limit=daily_limit,
        movements=[CoinMovementView(delta=m.delta, kind=m.kind, item=m.item, duel_id=str(m.duel_id) if m.duel_id else None,
                                    at=m.created_at) for m in wallet.movements],
        shop=[ShopItemView(key=i.key, label=i.text("label", language), description=i.text("description", language),
                           price=i.price, affordable=wallet.balance >= i.price) for i in r.shop],
        rules=CoinRulesView(starting_gift=r.starting_gift, strong_answer=r.strong_answer, strong_hard_answer=r.strong_hard_answer,
                            hard_difficulty_from=r.hard_difficulty_from, strong_interview_turn=r.strong_interview_turn,
                            max_hints_for_coins=r.max_hints_for_coins, duel_stake=r.duel_stake),
        enabled=wallet.enabled)


@router.get("", response_model=WalletView, summary="The caller's coins: balance, recent movements, the shop, the rules")
async def wallet(access: CurrentAccess, coins: Coins, practice: Practice,
                 language: str = Query("he", pattern="^(en|he)$")) -> WalletView:
    return _view(await coins.wallet(access.user_id), await practice._daily_limit(access.user_id), language)


@router.post("/buy", response_model=WalletView, summary="Spend coins on a shop item (402 when the balance is short)")
async def buy(body: BuyRequest, access: CurrentAccess, coins: Coins, practice: Practice,
              language: str = Query("he", pattern="^(en|he)$")) -> WalletView:
    wallet_after = await coins.buy(access.user_id, body.item)
    return _view(wallet_after, await practice._daily_limit(access.user_id), language)
