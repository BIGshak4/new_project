"""One practice attempt over HTTP (integration readiness §6).

    POST /v1/practice/attempts                                      start
    GET  /v1/practice/attempts/{id}                                 recover after a refresh
    POST /v1/practice/attempts/{id}/hints/next                      next hint
    POST /v1/practice/attempts/{id}/reference                       reveal the reference (recorded)
    POST /v1/practice/attempts/{id}/submissions                     the main answer
    POST /v1/practice/attempts/{id}/follow-ups/{turn}/submissions   a follow-up answer
    POST /v1/practice/attempts/{id}/submissions/{revision}/retry    re-evaluate a saved answer

Submissions carry an Idempotency-Key header (or `idempotency_key` in the body). Without
one the server generates it and returns it as `submission.key`, so a retry can reuse it.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Header, Path, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.deps import CurrentAccess, Practice
from app.api.errors import ApiError
from app.engine.practice import MAX_ANSWER_CHARS
from app.schemas.api import AttemptView, HintView, SubmissionView
from app.services.practice_service import PracticeService

router = APIRouter(prefix="/v1/practice/attempts", tags=["practice"])

# The answer is saved before the model is called. If the evaluation is not done within this budget the
# request answers 202 with the attempt in state "evaluating" while the evaluation continues in the
# background (shielded), and the client polls GET. Model calls have their own per-role deadlines.
RESPONSE_BUDGET_SECONDS = 90              # under Render's 100 s proxy limit


class StartAttemptRequest(BaseModel):
    question_key: str | None = Field(None, max_length=80)
    question_id: uuid.UUID | None = None
    mode: str = Field("deep", pattern="^(quick|deep)$")
    language: str | None = Field(None, pattern="^(en|he)$")
    self_confidence: int | None = Field(None, ge=1, le=5, description="1-5, asked before the question is shown")


class AnswerBody(BaseModel):
    text: str = Field(..., max_length=MAX_ANSWER_CHARS)


class SubmitRequest(BaseModel):
    answer: AnswerBody | str = Field(..., description="the answer text, or an object with a text field")
    idempotency_key: str | None = Field(None, min_length=1, max_length=128)
    latency_ms: int | None = Field(None, ge=0, description="time from question shown to submit, if measured")
    revision_count: int | None = Field(None, ge=0, description="how many times the answer was edited before submit")


class SubmissionResponse(BaseModel):
    submission: SubmissionView
    attempt: AttemptView


class HintResponse(BaseModel):
    hint: HintView | None                       # None when no hint is left (or the answer was already submitted)
    attempt: AttemptView


class ReferenceResponse(BaseModel):
    reference: str
    attempt: AttemptView


AttemptId = Annotated[uuid.UUID, Path(description="the attempt id returned when it was started")]
IdempotencyKey = Annotated[str | None, Header(alias="Idempotency-Key", max_length=128)]


def _key(header: str | None, body: SubmitRequest) -> str:
    return header or body.idempotency_key or str(uuid.uuid4())


def _answer(body: SubmitRequest):
    return body.answer if isinstance(body.answer, str) else {"text": body.answer.text}


_background: set[asyncio.Task] = set()


def _log_outcome(task: asyncio.Task) -> None:
    _background.discard(task)
    if not task.cancelled() and task.exception() is not None:
        logging.getLogger("app.practice").error("background evaluation failed: %r", task.exception())


async def _submit(practice: PracticeService, user_id: uuid.UUID, attempt_id: uuid.UUID, coroutine, *, turn: int | None = None):
    task = asyncio.ensure_future(coroutine)
    _background.add(task)
    task.add_done_callback(_log_outcome)
    try:
        submission, attempt = await asyncio.wait_for(asyncio.shield(task), timeout=RESPONSE_BUDGET_SECONDS)
    except TimeoutError:
        # still evaluating: report the saved answer as such; the task keeps running to completion
        attempt = await practice.get(user_id, attempt_id)
        pending = attempt.submission if turn is None else next(
            (f.submission for f in attempt.follow_ups if f.turn == turn), None)
        if pending is None:
            raise ApiError("evaluation_unavailable", "the evaluation is taking longer than usual; reload the attempt",
                           status=503) from None
        body = SubmissionResponse(submission=pending, attempt=attempt)
        return JSONResponse(body.model_dump(mode="json"), status_code=status.HTTP_202_ACCEPTED)
    return SubmissionResponse(submission=submission, attempt=attempt)


@router.post("", response_model=AttemptView, status_code=status.HTTP_201_CREATED, summary="Start an attempt",
             responses={404: {"description": "question unavailable"}, 429: {"description": "daily limit reached"}})
async def start(body: StartAttemptRequest, access: CurrentAccess, practice: Practice) -> AttemptView:
    if body.question_key is None and body.question_id is None:
        raise ApiError("validation", "question_key or question_id is required")
    return await practice.start(access.user_id, question_key=body.question_key, question_id=body.question_id,
                                mode=body.mode, language=body.language, self_confidence=body.self_confidence)


@router.get("/{attempt_id}", response_model=AttemptView, summary="The attempt as it is now (refresh-safe)")
async def get_attempt(attempt_id: AttemptId, access: CurrentAccess, practice: Practice) -> AttemptView:
    return await practice.get(access.user_id, attempt_id)


@router.post("/{attempt_id}/hints/next", response_model=HintResponse, summary="Show the next hint")
async def next_hint(attempt_id: AttemptId, access: CurrentAccess, practice: Practice) -> HintResponse:
    hint, attempt = await practice.next_hint(access.user_id, attempt_id)
    return HintResponse(hint=hint, attempt=attempt)


@router.post("/{attempt_id}/reference", response_model=ReferenceResponse,
             summary="Reveal the reference solution (answers accepted afterwards earn no evidence)")
async def reveal_reference(attempt_id: AttemptId, access: CurrentAccess, practice: Practice) -> ReferenceResponse:
    reference, attempt = await practice.reveal_reference(access.user_id, attempt_id)
    return ReferenceResponse(reference=reference, attempt=attempt)


@router.post("/{attempt_id}/submissions", response_model=SubmissionResponse, summary="Submit the answer",
             responses={202: {"description": "accepted, still evaluating: poll GET"}, 409: {"description": "conflict / already_submitted"},
                        503: {"description": "evaluation_unavailable"}})
async def submit(attempt_id: AttemptId, body: SubmitRequest, access: CurrentAccess, practice: Practice,
                 idempotency_key: IdempotencyKey = None) -> SubmissionResponse:
    return await _submit(practice, access.user_id, attempt_id,
                         practice.submit(access.user_id, attempt_id, _answer(body), idempotency_key=_key(idempotency_key, body),
                                         latency_ms=body.latency_ms, revision_count=body.revision_count))


@router.post("/{attempt_id}/follow-ups/{turn}/submissions", response_model=SubmissionResponse,
             summary="Answer the pending follow-up question",
             responses={409: {"description": "no_pending_follow_up / conflict"}})
async def submit_follow_up(attempt_id: AttemptId, turn: Annotated[int, Path(ge=1, le=9)], body: SubmitRequest,
                           access: CurrentAccess, practice: Practice, idempotency_key: IdempotencyKey = None) -> SubmissionResponse:
    return await _submit(practice, access.user_id, attempt_id,
                         practice.submit(access.user_id, attempt_id, _answer(body), idempotency_key=_key(idempotency_key, body),
                                         latency_ms=body.latency_ms, follow_up_turn=turn), turn=turn)


@router.post("/{attempt_id}/submissions/{revision}/retry", response_model=SubmissionResponse,
             summary="Evaluate a saved answer again after a failure",
             responses={409: {"description": "nothing_to_retry"}})
async def retry(attempt_id: AttemptId, revision: Annotated[int, Path(ge=1)], access: CurrentAccess,
                practice: Practice) -> SubmissionResponse:
    attempt = await practice.get(access.user_id, attempt_id)
    failed = [s for s in [attempt.submission, *[f.submission for f in attempt.follow_ups if f.submission]]
              if s is not None and s.status == "failed"]
    waiting = failed[-1] if failed else None                  # the engine retries the latest failed revision
    if waiting is None or waiting.revision != revision:
        raise ApiError("nothing_to_retry", f"revision {revision} is not waiting for evaluation")
    return await _submit(practice, access.user_id, attempt_id, practice.retry(access.user_id, attempt_id),
                         turn=waiting.turn or None)
