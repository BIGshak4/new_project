"""Duels (Shaked, 2026-10-22): open an invite, accept one by code, answer on the clock, read the result.

Two modes on the same routes. **quiz** (default): five American questions, a minute each at most; the view carries
`quiz` with the question in front of me (prompt and four options, never the correct one), the seconds left on it,
my score so far and how many my opponent has answered; when settled, `quiz.review` has every question with the
correct option, the explanation and both choices. **judged**: one bank question, three minutes, free text, the same
judge as practice; `question` and the bands as before.

Each player sees their own view: their own result as soon as it exists, the opponent's only when the duel is
settled. Coins move through the ledger (GET /v1/me/coins shows the stake, the payout or the refund). No XP, no
skill-profile change: a duel is a game on coins, and coins have no monetary value.

Status words: open (waiting for an opponent), active (clock running), settled, cancelled.
Outcome words once settled: challenger | opponent (that side won), draw (both refunded), forfeit_challenger |
forfeit_opponent (that side never answered; the other won), no_show (nobody answered; both refunded),
cancelled | expired (the invite was withdrawn or nobody accepted within a day; the challenger is refunded).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

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
    answered: bool = False                      # judged: sent an answer; quiz: finished every question
    band: str | None = None                     # judged — mine: once judged; the opponent's: once the duel is settled
    summary: str | None = None                  # the judge's one line, same visibility as the band
    submitted_at: datetime | None = None
    score: int | None = None                    # quiz — mine: live; the opponent's: once settled
    answered_count: int = 0                     # quiz: how many questions this side has answered (or let run out)
    seconds: float | None = None                # quiz: total answering time, once settled


class QuizItemView(BaseModel):
    index: int                                  # 0-based
    prompt: str
    choices: list[str]                          # four options, in the duel's language


class QuizAnswerView(BaseModel):
    index: int
    choice: int | None = None                   # None: the minute ran out
    correct: bool
    seconds: float


class QuizReviewView(BaseModel):
    index: int
    prompt: str
    choices: list[str]
    correct: int                                # the correct option, only once settled
    explanation: str
    mine: int | None = None
    theirs: int | None = None
    mine_correct: bool = False
    theirs_correct: bool = False


class QuizView(BaseModel):
    total: int                                  # questions in this duel (5)
    seconds_per_question: int                   # the ceiling per question (60)
    index: int                                  # the question in front of me (== total when I am finished)
    current: QuizItemView | None = None         # while the duel runs and I still have questions
    seconds_left: int | None = None             # on the current question
    answers: list[QuizAnswerView] = Field(default_factory=list)   # mine so far, with right/wrong
    score: int = 0
    finished: bool = False
    review: list[QuizReviewView] = Field(default_factory=list)    # once settled


class DuelView(BaseModel):
    id: str
    code: str                                   # the invite code; share_path is the link for the opponent
    share_path: str
    share_url: str
    status: str                                 # open | active | settled | cancelled
    mode: str                                   # quiz | judged
    role: str                                   # challenger | opponent
    stake: int
    pot: int
    language: str
    question: DuelQuestionView | None = None    # judged: only while the duel is active
    quiz: QuizView | None = None                # quiz: from acceptance on
    deadline: datetime | None = None            # the whole duel's end
    seconds_left: int | None = None             # on the whole duel while active
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
    rules: dict                                 # stake, mode_default, quiz numbers, clock, cooldown, caps


class CreateDuelRequest(BaseModel):
    language: str = Field("he", pattern="^(en|he)$")
    mode: str | None = Field(None, pattern="^(quiz|judged)$")   # default: the seed's mode_default (quiz)


class AcceptDuelRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=16)


class DuelAnswerRequest(BaseModel):
    text: str | None = Field(None, min_length=1, max_length=20_000)   # judged
    choice: int | None = Field(None, ge=0, le=3)                      # quiz: the option pressed
    item: int | None = Field(None, ge=0)                              # quiz: the question index on the screen (a stale-screen guard)


def _quiz_view(svc, duel: Duel, user_id: uuid.UUID, settled: bool) -> QuizView | None:
    if duel.mode != "quiz" or not duel.items:
        return None
    language = duel.language
    me = duel.players.get(str(user_id), {})
    other = duel.players.get(str(duel.other(user_id)), {}) if duel.other(user_id) else {}
    answers = list(me.get("answers", []))
    index = len(answers)
    limit = svc.rules.duel_quiz_seconds
    current, seconds_left = None, None
    if duel.status == "active" and index < len(duel.items) and me.get("opened_at"):
        q = svc.quiz.get(duel.items[index]["key"])
        current = (QuizItemView(index=index, prompt=q.text(q.prompt, language), choices=[q.text(c, language) for c in q.choices])
                   if q else QuizItemView(index=index, prompt="(this question was removed)", choices=["", "", "", ""]))
        opened = datetime.fromisoformat(me["opened_at"])
        seconds_left = max(0, int((opened + timedelta(seconds=limit) - svc.clock()).total_seconds()))
    review = []
    if settled:
        theirs = list(other.get("answers", []))
        for i, item in enumerate(duel.items):
            q = svc.quiz.get(item["key"])
            if q is None:
                continue
            mine = answers[i] if i < len(answers) else {}
            his = theirs[i] if i < len(theirs) else {}
            review.append(QuizReviewView(index=i, prompt=q.text(q.prompt, language), choices=[q.text(c, language) for c in q.choices],
                                         correct=q.correct, explanation=q.text(q.explanation, language),
                                         mine=mine.get("choice"), theirs=his.get("choice"),
                                         mine_correct=bool(mine.get("correct")), theirs_correct=bool(his.get("correct"))))
    return QuizView(total=len(duel.items), seconds_per_question=limit, index=index, current=current, seconds_left=seconds_left,
                    answers=[QuizAnswerView(index=i, choice=a.get("choice"), correct=bool(a.get("correct")), seconds=float(a.get("seconds", 0)))
                             for i, a in enumerate(answers)],
                    score=sum(1 for a in answers if a.get("correct")), finished=me.get("status") in ("done", "absent"),
                    review=review)


def _view(svc, duel: Duel, user_id: uuid.UUID) -> DuelView:
    me_id, other_id = user_id, duel.other(user_id)
    settled = duel.status == "settled"
    mine = duel.players.get(str(me_id), {})
    theirs = duel.players.get(str(other_id), {}) if other_id else {}

    def side(p: dict, *, reveal: bool) -> DuelSideView:
        done = p.get("status") == "done"
        answers = p.get("answers")
        if duel.mode == "quiz":
            count = len(answers or [])
            return DuelSideView(answered=p.get("status") in ("done", "absent"), answered_count=count,
                                score=(sum(1 for a in answers or [] if a.get("correct")) if reveal else None),
                                seconds=p.get("seconds") if reveal and settled else None)
        return DuelSideView(answered=bool(p.get("submitted_at")) or done, band=p.get("band") if reveal and done else None,
                            summary=p.get("summary") if reveal and done else None,
                            submitted_at=datetime.fromisoformat(p["submitted_at"]) if p.get("submitted_at") and reveal else None)

    question = None
    q = svc.catalog.questions.get(duel.question_key) if duel.mode == "judged" and duel.status == "active" else None
    if q is not None:
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
                    status=duel.status, mode=duel.mode, role="challenger" if me_id == duel.challenger_id else "opponent",
                    stake=duel.stake, pot=duel.stake * players, language=duel.language, question=question,
                    quiz=_quiz_view(svc, duel, user_id, settled),
                    deadline=duel.deadline, seconds_left=seconds_left, me=side(mine, reveal=True),
                    opponent=side(theirs, reveal=settled) if other_id else None, outcome=duel.outcome, won=won,
                    coins_delta=delta, created_at=duel.created_at, accepted_at=duel.accepted_at, settled_at=duel.settled_at)


def _rules(svc) -> dict:
    r = svc.rules
    return {"stake": r.duel_stake, "mode_default": r.duel_mode_default, "quiz_questions": r.duel_quiz_questions,
            "quiz_seconds_per_question": r.duel_quiz_seconds, "quiz_available": len(svc.quiz_pool()) >= r.duel_quiz_questions,
            "clock_seconds": r.duel_clock_seconds, "cooldown_minutes": r.duel_cooldown_minutes,
            "daily_earning_cap": r.duel_daily_earning_cap, "daily_cap": r.duel_daily_cap, "no_monetary_value": True}


@router.get("", response_model=DuelListView, summary="My duels, newest first (overdue ones are settled on the way)")
async def list_duels(access: CurrentAccess, duels: Duels, limit: int = Query(20, ge=1, le=50)) -> DuelListView:
    rows = await duels.list(access.user_id, limit=limit)
    return DuelListView(duels=[_view(duels, d, access.user_id) for d in rows], rules=_rules(duels))


@router.post("", response_model=DuelView, status_code=201, summary="Open a duel: stake 5 coins, get an invite code")
async def create_duel(body: CreateDuelRequest, access: CurrentAccess, duels: Duels) -> DuelView:
    return _view(duels, await duels.create(access.user_id, language=body.language, mode=body.mode), access.user_id)


@router.post("/accept", response_model=DuelView, summary="Accept an invite by code: stake 5, the questions appear, the clock starts")
async def accept_duel(body: AcceptDuelRequest, access: CurrentAccess, duels: Duels) -> DuelView:
    return _view(duels, await duels.accept(access.user_id, body.code), access.user_id)


@router.get("/{duel_id}", response_model=DuelView, summary="One duel as I see it")
async def get_duel(duel_id: uuid.UUID, access: CurrentAccess, duels: Duels) -> DuelView:
    return _view(duels, await duels.get(access.user_id, duel_id), access.user_id)


@router.post("/{duel_id}/answer", response_model=DuelView,
             summary="Quiz: {choice, item} for the question in front of me. Judged: {text}, scored on the spot")
async def answer_duel(duel_id: uuid.UUID, body: DuelAnswerRequest, access: CurrentAccess, duels: Duels) -> DuelView:
    return _view(duels, await duels.answer(access.user_id, duel_id, body.text, choice=body.choice, item=body.item), access.user_id)


@router.post("/{duel_id}/cancel", response_model=DuelView, summary="Withdraw my open invite (the stake comes back)")
async def cancel_duel(duel_id: uuid.UUID, access: CurrentAccess, duels: Duels) -> DuelView:
    return _view(duels, await duels.cancel(access.user_id, duel_id), access.user_id)
