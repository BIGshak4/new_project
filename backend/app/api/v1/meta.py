"""Reference lists the app needs before anything else: job types to choose from, companies people reported."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import CurrentAccess, Practice
from app.schemas.api import CompanyView, JobTypeView

router = APIRouter(prefix="/v1", tags=["meta"])


@router.get("/job-types", response_model=list[JobTypeView], summary="The job types a candidate can prepare for")
async def job_types(access: CurrentAccess, practice: Practice,
                    language: str = Query("en", pattern="^(en|he)$")) -> list[JobTypeView]:
    return practice.job_types(language=language)


@router.get("/companies", response_model=list[CompanyView], summary="Companies where questions were reported")
async def companies(access: CurrentAccess, practice: Practice) -> list[CompanyView]:
    return await practice.companies()
