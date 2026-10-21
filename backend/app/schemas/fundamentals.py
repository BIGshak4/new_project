"""Self-reported completion of short study cards; never a correctness grade."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FundamentalsCompletion(BaseModel):
    model_config = ConfigDict(frozen=True)

    question_key: str
    content_revision: str
    completed_at: datetime


class FundamentalsProgress(BaseModel):
    completed: list[FundamentalsCompletion] = Field(default_factory=list)


class CompleteFundamentalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_revision: str = Field(pattern=r"^[a-f0-9]{64}$")


class RemoveFundamentalResponse(BaseModel):
    removed: bool
