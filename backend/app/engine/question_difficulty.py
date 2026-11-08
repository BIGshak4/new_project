"""Attach internal editorial ratings to the exact bank revisions that were reviewed."""

import hashlib
import json
from pathlib import Path

RATINGS = Path(__file__).resolve().parents[2] / "seeds" / "question_difficulty.json"


def difficulty_fingerprint(question: dict) -> str:
    assets = question["assets"]
    inputs = {
        "text": {lang: {k: t.get(k) for k in ("prompt", "requirements", "reference_solution", "choices")}
                 for lang, t in question["translations"].items()},
        "code": assets.get("shared_code"),
        "correct_choice": question.get("correct_choice"),
        "prompt_media": sorted(m["sha256"] for m in assets.get("bank_media", []) if m["role"] == "prompt"),
    }
    return hashlib.sha256(json.dumps(inputs, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def apply_question_difficulty(questions: list[dict]) -> None:
    ratings = json.loads(RATINGS.read_text(encoding="utf-8"))
    for q in questions:
        key = q["key"]
        rating = ratings.get(key)
        if not rating or rating["content_sha256"] != difficulty_fingerprint(q):
            raise ValueError(f"{key}: review the current prompt and answer before assigning its difficulty")
        score = rating["difficulty"]
        if type(score) is not int or not 1 <= score <= 10 or not rating["reason"].strip():
            raise ValueError(f"{key}: expected an integer difficulty from 1 to 10 and its rationale")
        q["difficulty"] = score
        q["assets"]["difficulty_status"] = "rated"
