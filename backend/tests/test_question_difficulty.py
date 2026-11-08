import json
from copy import deepcopy

import pytest

from app.engine.question_difficulty import RATINGS, apply_question_difficulty, difficulty_fingerprint


def test_compiled_banks_match_all_reviewed_question_revisions():
    ratings = json.loads(RATINGS.read_text(encoding="utf-8"))
    bank = [q for name in ("example_bank", "preparation_bank")
            for q in json.loads((RATINGS.parent / "questions" / f"{name}.json").read_text(encoding="utf-8"))]
    assert len(bank) == len(ratings)
    assert {q["key"] for q in bank} == set(ratings)
    for q in bank:
        entry = ratings[q["key"]]
        assert type(entry["difficulty"]) is int and 1 <= entry["difficulty"] <= 10 and entry["reason"].strip()
        assert (q["difficulty"], q["assets"]["difficulty_status"]) == (entry["difficulty"], "rated")
        assert entry["content_sha256"] == difficulty_fingerprint(q)


def test_changed_answer_cannot_inherit_rating():
    bank = json.loads((RATINGS.parent / "questions/example_bank.json").read_text(encoding="utf-8"))
    changed = deepcopy(bank[0])
    changed["translations"]["he"]["reference_solution"] += " revised"
    with pytest.raises(ValueError, match="review the current prompt and answer"):
        apply_question_difficulty([changed])
