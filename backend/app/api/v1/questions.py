"""The question catalog, in the safe shape (no answers, no hidden hints)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.api.deps import CurrentAccess, Practice
from app.repo.questions import QuestionDetail, QuestionSummary

router = APIRouter(prefix="/v1/questions", tags=["questions"])


@router.get("", response_model=list[QuestionSummary], summary="List the questions available to practise")
async def list_questions(access: CurrentAccess, practice: Practice, language: str = Query("en", pattern="^(en|he)$"),
                         subject: str | None = Query(None, max_length=80)) -> list[QuestionSummary]:
    return await practice.list_questions(language=language, subject=subject)


@router.get("/{key_or_id}", response_model=QuestionDetail, summary="One question: prompt, code, choices",
            responses={404: {"description": "unknown, unpublished or not enriched"}})
async def get_question(key_or_id: str, access: CurrentAccess, practice: Practice,
                       language: str = Query("en", pattern="^(en|he)$")) -> QuestionDetail:
    try:
        question_id = uuid.UUID(key_or_id)
    except ValueError:
        return await practice.get_question(language=language, key=key_or_id)
    return await practice.get_question(language=language, question_id=question_id)
