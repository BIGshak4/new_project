"""Human approval of a solution is independent of assessment/publication approval.

The founder attested to the existing solutions on 2026-10-21. The attestation is
bound to that content snapshot; adding or editing a question cannot inherit it.
No reviewer identity, credential, difficulty calibration, reuse permission or
Hebrew/English parity approval is implied by this metadata.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Literal

from pydantic import BaseModel


class SolutionReview(BaseModel):
    status: Literal["human_reviewed", "pending_review"] = "pending_review"
    reviewed_on: str | None = None


def solution_content_hash(question) -> str:
    """Version 1: question, answer and learner-visible solution support content.

    Ignore operational/review metadata and private source screenshots. Include
    authored illustration/code identities and captions, so replacing a diagram
    or changing the meaning of the prompt invalidates the approval too.
    """
    data = question.model_dump(mode="json") if hasattr(question, "model_dump") else question
    assets = data.get("assets") or {}
    resource = assets.get("preparation_resource") or {}
    media_fields = ("path", "sha256", "role", "kind", "caption", "language")
    media = [
        {key: item.get(key) for key in media_fields}
        for item in assets.get("bank_media") or []
        if not str(item.get("source_path", "")).replace("\\", "/").startswith("sources/")
    ]
    payload = {
        "schema_version": 1,
        "key": data["key"],
        "correct_choice": data.get("correct_choice"),
        "translations": {
            lang: {"prompt": text["prompt"], "reference_solution": text["reference_solution"],
                   "choices": text.get("choices") or None}
            for lang, text in sorted(data["translations"].items())
        },
        "shared_code": assets.get("shared_code"),
        "code_language": assets.get("code_language"),
        "learner_material": resource.get("learner_material"),
        "media": sorted(media, key=lambda item: str(item["path"])),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def solution_review(question) -> SolutionReview:
    data = question.model_dump(mode="json") if hasattr(question, "model_dump") else question
    record = (data.get("assets") or {}).get("solution_review") or {}
    if not isinstance(record, dict):
        return SolutionReview()
    if (record.get("schema_version") != 1 or record.get("status") != "human_reviewed"
            or record.get("basis") != "user_attestation"
            or record.get("content_sha256") != solution_content_hash(data)):
        return SolutionReview()
    try:
        reviewed_on = date.fromisoformat(record["reviewed_on"]).isoformat()
    except (KeyError, TypeError, ValueError):
        return SolutionReview()
    return SolutionReview(status="human_reviewed", reviewed_on=reviewed_on)


def attach_registered_reviews(questions: list[dict], registry: dict) -> None:
    """Apply only frozen, matching attestations. Never approve a new revision."""
    records = registry.get("questions", {})
    for question in questions:
        record = records.get(question["key"])
        assets = question.setdefault("assets", {})
        assets.pop("solution_review", None)
        if record and record.get("content_sha256") == solution_content_hash(question):
            assets["solution_review"] = dict(record)
