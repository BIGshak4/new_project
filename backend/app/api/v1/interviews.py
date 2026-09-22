"""Mock interviews over HTTP.

    POST /v1/interviews                                   start (duration, language)
    GET  /v1/interviews                                   my interviews, newest first
    GET  /v1/interviews/{id}                              the interview as it is now (refresh-safe)
    POST /v1/interviews/{id}/turns/{turn}/answer          answer the current question
    POST /v1/interviews/{id}/hints/next                   ask for a hint (coach mode)
    POST /v1/interviews/{id}/end                          stop early; the report covers what was answered
    GET  /v1/interviews/{id}/report                       scorecards, per-skill levels, narrative

Answers carry an Idempotency-Key header (or `idempotency_key` in the body): the same key returns the
same result, a different key for an answered question is a 409. Results (bands, summaries) are hidden
until the interview is over; the report reveals them.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Header, Path, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.deps import CurrentAccess, Interview
from app.api.errors import ApiError
from app.schemas.api import HintView, InterviewListItem, InterviewReportView, InterviewTurnView, InterviewView
from app.services.interview_service import DURATIONS, InterviewService

router = APIRouter(prefix="/v1/interviews", tags=["interviews"])

RESPONSE_BUDGET_SECONDS = 90              # under Render's 100 s proxy limit; the evaluation continues in the background
REPORT_BUDGET_SECONDS = 75                # the narrative is written by the model; past this, the plain report is returned


class StartInterviewRequest(BaseModel):
    duration_min: int = Field(30, description=f"one of {', '.join(map(str, DURATIONS))}")
    language: str | None = Field(None, pattern="^(en|he)$")


class InterviewAnswerRequest(BaseModel):
    answer: str | dict = Field(..., description="the answer text, or an object with a text field")
    idempotency_key: str | None = Field(None, min_length=1, max_length=128)
    latency_ms: int | None = Field(None, ge=0, description="time from question shown to submit, if measured")


class InterviewAnswerResponse(BaseModel):
    turn: InterviewTurnView
    interview: InterviewView


class InterviewHintResponse(BaseModel):
    hint: HintView | None
    interview: InterviewView


InterviewId = Annotated[uuid.UUID, Path(description="the interview id returned when it was started")]
IdempotencyKey = Annotated[str | None, Header(alias="Idempotency-Key", max_length=128)]

_background: set[asyncio.Task] = set()
log = logging.getLogger("app.interview")


def _done(task: asyncio.Task) -> None:
    _background.discard(task)
    if not task.cancelled() and task.exception() is not None:
        log.error("background interview task failed: %r", task.exception())


@router.post("", response_model=InterviewView, status_code=status.HTTP_201_CREATED, summary="Start a mock interview",
             responses={409: {"description": "no reviewed questions for this role yet"}, 429: {"description": "daily limit"}})
async def start(body: StartInterviewRequest, access: CurrentAccess, interviews: Interview) -> InterviewView:
    return await interviews.start(access.user_id, duration_min=body.duration_min, language=body.language)


@router.get("", response_model=list[InterviewListItem], summary="My interviews, newest first")
async def list_interviews(access: CurrentAccess, interviews: Interview) -> list[InterviewListItem]:
    return [InterviewListItem(**row) for row in await interviews.list(access.user_id)]


@router.get("/{interview_id}", response_model=InterviewView, summary="The interview as it is now (refresh-safe)")
async def get_interview(interview_id: InterviewId, access: CurrentAccess, interviews: Interview) -> InterviewView:
    return await interviews.get(access.user_id, interview_id)


@router.post("/{interview_id}/turns/{turn_index}/answer", response_model=InterviewAnswerResponse,
             summary="Answer the current question",
             responses={202: {"description": "saved; still being evaluated, poll GET"},
                        409: {"description": "already answered or the interview is over"}})
async def answer(interview_id: InterviewId, turn_index: Annotated[int, Path(ge=0)], body: InterviewAnswerRequest,
                 access: CurrentAccess, interviews: Interview, idempotency_key: IdempotencyKey = None):
    key = idempotency_key or body.idempotency_key or str(uuid.uuid4())
    task = asyncio.ensure_future(interviews.answer(access.user_id, interview_id, turn_index, body.answer,
                                                   idempotency_key=key, latency_ms=body.latency_ms))
    _background.add(task)
    task.add_done_callback(_done)
    try:
        turn, interview = await asyncio.wait_for(asyncio.shield(task), timeout=RESPONSE_BUDGET_SECONDS)
    except TimeoutError:
        interview = await interviews.get(access.user_id, interview_id)
        pending = interview.current_turn
        if pending is None or pending.index != turn_index:
            raise ApiError("evaluation_unavailable", "the evaluation is taking longer than usual; reload the interview",
                           status=503) from None
        body_out = InterviewAnswerResponse(turn=pending, interview=interview)
        return JSONResponse(body_out.model_dump(mode="json"), status_code=status.HTTP_202_ACCEPTED)
    return InterviewAnswerResponse(turn=turn, interview=interview)


@router.post("/{interview_id}/hints/next", response_model=InterviewHintResponse, summary="Ask for a hint")
async def hint(interview_id: InterviewId, access: CurrentAccess, interviews: Interview) -> InterviewHintResponse:
    given, interview = await interviews.hint(access.user_id, interview_id)
    return InterviewHintResponse(hint=given, interview=interview)


@router.post("/{interview_id}/end", response_model=InterviewView, summary="End the interview early")
async def end(interview_id: InterviewId, access: CurrentAccess, interviews: Interview) -> InterviewView:
    return await interviews.end(access.user_id, interview_id)


@router.get("/{interview_id}/report", response_model=InterviewReportView, summary="The report of a finished interview",
            responses={409: {"description": "the interview is still running"}})
async def report(interview_id: InterviewId, access: CurrentAccess, interviews: Interview) -> InterviewReportView:
    task = asyncio.ensure_future(interviews.report(access.user_id, interview_id))
    _background.add(task)
    task.add_done_callback(_done)
    try:
        return await asyncio.wait_for(asyncio.shield(task), timeout=REPORT_BUDGET_SECONDS)
    except TimeoutError:
        # the model is still writing the narrative: hand back the plain report now, the narrative lands for the next call
        return await interviews.report(access.user_id, interview_id, narrative=False)


__all__ = ["router", "InterviewService"]
