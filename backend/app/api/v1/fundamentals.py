"""Authenticated, self-reported completion history for the short fundamentals cards."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request

from app.api.deps import CurrentAccess
from app.api.errors import ApiError
from app.schemas.fundamentals import (
    CompleteFundamentalRequest,
    FundamentalsCompletion,
    FundamentalsProgress,
    RemoveFundamentalResponse,
)
from app.services.fundamentals import FundamentalsService

router = APIRouter(prefix="/v1/fundamentals/progress", tags=["fundamentals"])


def fundamentals_service(request: Request) -> FundamentalsService:
    runtime = getattr(request.app.state, "runtime", None)
    service = getattr(runtime, "fundamentals", None)
    if service is None:
        raise ApiError("temporarily_unavailable", "short-practice history is temporarily unavailable", status=503)
    return service


Fundamentals = Annotated[FundamentalsService, Depends(fundamentals_service)]
QuestionKey = Annotated[str, Path(pattern=r"^[a-z0-9][a-z0-9-]{0,95}$")]


@router.get("", response_model=FundamentalsProgress, summary="The caller's short-study completion history")
async def get_progress(access: CurrentAccess, fundamentals: Fundamentals) -> FundamentalsProgress:
    return await fundamentals.progress(access.user_id)


@router.put("/{question_key}", response_model=FundamentalsCompletion,
            summary="Mark a known short-card revision finished (self-reported, no grade)")
async def complete(question_key: QuestionKey, body: CompleteFundamentalRequest,
                   access: CurrentAccess, fundamentals: Fundamentals) -> FundamentalsCompletion:
    return await fundamentals.complete(access.user_id, question_key, body.content_revision)


@router.delete("/{question_key}", response_model=RemoveFundamentalResponse,
               summary="Remove the caller's own completion marker")
async def remove(question_key: QuestionKey, access: CurrentAccess,
                 fundamentals: Fundamentals) -> RemoveFundamentalResponse:
    return RemoveFundamentalResponse(removed=await fundamentals.remove(access.user_id, question_key))
