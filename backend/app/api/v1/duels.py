"""Duels (Shaked, 2026-10-22): open an invite, accept one by code, answer on the clock, read the result.

Each player sees their own view: the question only while the duel runs, their own band once judged, the opponent's
band only when the duel is settled. Coins move through the ledger (GET /v1/me/coins shows the stake, the payout or
the refund). No XP, no skill-profile change: a duel is a game on coins, and coins have no monetary value.

Status words: open (waiting for an opponent), active (clock running), settled, cancelled.
Outcome words once settled: challenger | opponent (that side won), draw (both refunded), forfeit_challenger |
forfeit_opponent (that side never answered; the other won), no_show (nobody answered; both refunded),
cancelled | expired (the invite was withdrawn or nobody accepted within a day; the challenger is refunded).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.deps import CurrentAccess, Duels
from app.repo.duels import Duel

router = APIRouter(prefix="/v1/duels", tags=["duels"])


class DuelQuestionView(BaseModel):
    key: str
    title: str
    prompt: str                                 # the question with its shared code block, in the duel's language
    format: str
    difficulty: int


class DuelSideView(BaseModel):
    answered: bool = False
    band: str | None = None                     # mine: once judged; the opponent's: once the duel is settled
    summary: str | None = None                  # the judge's one line, same visibility as the band
    submitted_at: datetime | None = None


class DuelView(BaseModel):
    id: str
    code: str                                   # the invite code; share_path is the link for the opponent
    share_path: str
    share_url: str
    status: str                                 # open | active | settled | cancelled
    role: str                                   # challenger | opponent
    stake: int
    pot: int
    language: str
    question: DuelQuestionView | None = None    # only while the duel is active
    deadline: datetime | None = None
    seconds_left: int | None = None             # while active; 0 when the clock ran out and the next read settles it
    me: DuelSideView
    opponent: DuelSideView | None = None        # None while nobody accepted
    outcome: str | None = None                  # see the module docstring
    won: bool | None = None                     # for me: True won, False lost, None draw/refund/not settled
    coins_delta: int | None = None              # what this duel did to my balance, once settled (+5, -5 or 0)
    created_at: datetime
    accepted_at: datetime | None = None
    settled_at: datetime | None = None


class DuelListView(BaseModel):
    duels: list[DuelView] = Field(default_factory=list)
    rules: dict                                 # stake, clock_seconds, cooldown_minutes, daily_earning_cap, daily_cap


class CreateDuelRequest(BaseModel):
    language: str = Field("he", pattern="^(en|he)$")


class AcceptDuelRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=16)


class DuelAnswerRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20_000)


def _view(svc, duel: Duel, user_id: uuid.UUID) -> DuelView:
    me_id, other_id = user_id, duel.other(user_id)
    settled = duel.status == "settled"
    mine = duel.players.get(str(me_id), {})
    theirs = duel.players.get(str(other_id), {}) if other_id else {}

    def side(p: dict, *, reveal: bool) -> DuelSideView:
        done = p.get("status") == "done"
        return DuelSideView(answered=bool(p.get("submitted_at")) or done, band=p.get("band") if reveal and done else None,
                            summary=p.get("summary") if reveal and done else None,
                            submitted_at=datetime.fromisoformat(p["submitted_at"]) if p.get("submitted_at") and reveal else None)

    question = None
    if duel.status == "active" and duel.question_key:
        q = svc.catalog.questions[duel.question_key]
        question = DuelQuestionView(key=q.key, title=q.text(duel.language).title, prompt=q.prompt_with_code(duel.language),
                                    format=q.format, difficulty=q.difficulty)
    seconds_left = None
    if duel.status == "active" and duel.deadline is not None:
        seconds_left = max(0, int((duel.deadline - svc.clock()).total_seconds()))
    won = None
    delta = None
    if settled or duel.status == "cancelled":
        if duel.winner_id is not None:
            won = duel.winner_id == me_id
            delta = duel.stake if won else -duel.stake
        else:
            delta = 0
    players = 2 if duel.opponent_id else 1
    return DuelView(id=str(duel.id), code=duel.code, share_path=svc.share_path(duel), share_url=svc.share_url(duel),
                    status=duel.status, role="challenger" if me_id == duel.challenger_id else "opponent",
                    stake=duel.stake, pot=duel.stake * players, language=duel.language, question=question,
                    deadline=duel.deadline, seconds_left=seconds_left, me=side(mine, reveal=True),
                    opponent=side(theirs, reveal=settled) if other_id else None, outcome=duel.outcome, won=won,
                    coins_delta=delta, created_at=duel.created_at, accepted_at=duel.accepted_at, settled_at=duel.settled_at)


def _rules(svc) -> dict:
    r = svc.rules
    return {"stake": r.duel_stake, "clock_seconds": r.duel_clock_seconds, "cooldown_minutes": r.duel_cooldown_minutes,
            "daily_earning_cap": r.duel_daily_earning_cap, "daily_cap": r.duel_daily_cap, "no_monetary_value": True}


@router.get("", response_model=DuelListView, summary="My duels, newest first (overdue ones are settled on the way)")
async def list_duels(access: CurrentAccess, duels: Duels, limit: int = Query(20, ge=1, le=50)) -> DuelListView:
    rows = await duels.list(access.user_id, limit=limit)
    return DuelListView(duels=[_view(duels, d, access.user_id) for d in rows], rules=_rules(duels))


@router.post("", response_model=DuelView, status_code=201, summary="Open a duel: stake 5 coins, get an invite code")
async def create_duel(body: CreateDuelRequest, access: CurrentAccess, duels: Duels) -> DuelView:
    return _view(duels, await duels.create(access.user_id, language=body.language), access.user_id)


@router.post("/accept", response_model=DuelView, summary="Accept an invite by code: stake 5, the question appears, the clock starts")
async def accept_duel(body: AcceptDuelRequest, access: CurrentAccess, duels: Duels) -> DuelView:
    return _view(duels, await duels.accept(access.user_id, body.code), access.user_id)


@router.get("/{duel_id}", response_model=DuelView, summary="One duel as I see it")
async def get_duel(duel_id: uuid.UUID, access: CurrentAccess, duels: Duels) -> DuelView:
    return _view(duels, await duels.get(access.user_id, duel_id), access.user_id)


@router.post("/{duel_id}/answer", response_model=DuelView, summary="My one answer, judged on the spot; settles when both are in")
async def answer_duel(duel_id: uuid.UUID, body: DuelAnswerRequest, access: CurrentAccess, duels: Duels) -> DuelView:
    return _view(duels, await duels.answer(access.user_id, duel_id, body.text), access.user_id)


@router.post("/{duel_id}/cancel", response_model=DuelView, summary="Withdraw my open invite (the stake comes back)")
async def cancel_duel(duel_id: uuid.UUID, access: CurrentAccess, duels: Duels) -> DuelView:
    return _view(duels, await duels.cancel(access.user_id, duel_id), access.user_id)
