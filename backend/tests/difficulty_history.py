"""Validate current ratings before projecting the bank onto pre-rating content hashes."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from tests.copy_november12_history import before_current_copy
ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def historical_scores():
    ratings = json.loads((ROOT / "backend/seeds/question_difficulty.json").read_bytes())
    source = json.loads((ROOT / "example_question/questions.json").read_bytes())
    examples = {f"example-{q['key']}": q["difficulty"] for q in source["questions"]}
    return ratings, examples


def before_difficulty_review(question):
    if question["key"].startswith("example-"):
        question = before_current_copy("example", f"compiled:{question['key']}", question)
    ratings, examples = historical_scores()
    key = question["key"]
    assert type(question["difficulty"]) is int, key
    if question["difficulty"] != ratings[key]["difficulty"]:
        frozen = json.loads((ROOT / "backend/tests/fixtures/preparation_before_20261108_batch20.json").read_bytes())
        historical = frozen["difficulty_ratings"][key]
        digest = hashlib.sha256(json.dumps(question, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        assert question["difficulty"] == historical["difficulty"], key
        assert digest == frozen["compiled_sha256"][key], key
    assets = question["assets"].copy()
    assert assets.pop("difficulty_status") == "rated", key
    previous = {**question, "assets": assets}
    if key in examples:
        previous["difficulty"] = examples[key]
    else:
        previous["difficulty"] = 5
        assets["difficulty_status"] = "unrated"
        note = "Imported for founder pilot. Technical review, rubric and reuse review pending. No mastery evidence or competitive XP."
        assert previous["review_notes"] == note, key
        previous["review_notes"] = note.replace("Technical review", "Difficulty, technical review")
    return previous
