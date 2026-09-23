"""The question catalog, in the safe shape (no answers, no hidden hints)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.deps import CurrentAccess, Practice
from app.repo.questions import CompanyTag, QuestionDetail, QuestionSummary

router = APIRouter(prefix="/v1/questions", tags=["questions"])


class SightingRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=80, description="the company where this question was asked")


class SightingResponse(BaseModel):
    companies: list[CompanyTag]


@router.get("", response_model=list[QuestionSummary],
            summary="List the questions available to practise (filter by subject, job type, company)")
async def list_questions(access: CurrentAccess, practice: Practice, language: str = Query("en", pattern="^(en|he)$"),
                         subject: str | None = Query(None, max_length=80),
                         job: str | None = Query(None, max_length=40, description="a job type key; sorts by relevance"),
                         company: str | None = Query(None, max_length=80, description="a company name or slug")
                         ) -> list[QuestionSummary]:
    return await practice.list_questions(language=language, subject=subject, job=job, company=company)


@router.post("/{key_or_id}/sightings", response_model=SightingResponse, summary="'I saw this question at company X'",
             responses={404: {"description": "unknown question"}, 503: {"description": "company tags not enabled yet"}})
async def add_sighting(key_or_id: str, body: SightingRequest, access: CurrentAccess, practice: Practice) -> SightingResponse:
    try:
        question_id = uuid.UUID(key_or_id)
    except ValueError:
        tags = await practice.add_sighting(access.user_id, company=body.company, key=key_or_id)
    else:
        tags = await practice.add_sighting(access.user_id, company=body.company, question_id=question_id)
    return SightingResponse(companies=tags)


@router.get("/{key_or_id}", response_model=QuestionDetail, summary="One question: prompt, code, choices",
            responses={404: {"description": "unknown, unpublished or not enriched"}})
async def get_question(key_or_id: str, access: CurrentAccess, practice: Practice,
                       language: str = Query("en", pattern="^(en|he)$")) -> QuestionDetail:
    try:
        question_id = uuid.UUID(key_or_id)
    except ValueError:
        return await practice.get_question(language=language, key=key_or_id)
    return await practice.get_question(language=language, question_id=question_id)
