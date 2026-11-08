"""Validate current ratings before projecting the bank onto pre-rating content hashes."""
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def historical_scores():
    ratings = json.loads((ROOT / "backend/seeds/question_difficulty.json").read_bytes())
    source = json.loads((ROOT / "example_question/questions.json").read_bytes())
    examples = {f"example-{q['key']}": q["difficulty"] for q in source["questions"]}
    return ratings, examples


def before_difficulty_review(question):
    ratings, examples = historical_scores()
    key = question["key"]
    assert type(question["difficulty"]) is int and question["difficulty"] == ratings[key]["difficulty"], key
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
