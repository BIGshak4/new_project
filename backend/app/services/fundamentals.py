"""Short self-study completion, separate from graded attempts, evidence, XP and limits."""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from app.api.errors import ApiError
from app.repo.fundamentals import FundamentalsRepository
from app.schemas.fundamentals import FundamentalsCompletion, FundamentalsProgress


def load_fundamentals_catalog(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    revisions = data.get("questions")
    if data.get("schema_version") != 1 or not isinstance(revisions, dict) or not revisions:
        raise ValueError("Fundamentals catalog is missing or invalid; rebuild it from the authored cards")
    for key, revision in revisions.items():
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,95}", key) or not re.fullmatch(r"[a-f0-9]{64}", revision):
            raise ValueError("Fundamentals catalog has an invalid key or content revision")
    return dict(revisions)


class FundamentalsService:
    def __init__(self, repository: FundamentalsRepository, revisions: dict[str, str]):
        self.repository = repository
        self.revisions = dict(revisions)

    def _known(self, question_key: str) -> str:
        revision = self.revisions.get(question_key)
        if revision is None:
            raise ApiError("not_found", "this short-practice question does not exist")
        return revision

    async def progress(self, user_id: uuid.UUID) -> FundamentalsProgress:
        # Keep older revisions: the UI can distinguish 'finished an earlier
        # version' from 'finished the current question' without losing history.
        return FundamentalsProgress(completed=await self.repository.list_completed(user_id))

    async def complete(self, user_id: uuid.UUID, question_key: str,
                       content_revision: str) -> FundamentalsCompletion:
        if content_revision != self._known(question_key):
            raise ApiError("stale_version", "this short-practice question changed; reload before marking it finished")
        return await self.repository.complete(user_id, question_key, content_revision)

    async def remove(self, user_id: uuid.UUID, question_key: str) -> bool:
        self._known(question_key)
        return await self.repository.remove(user_id, question_key)
