"""Regression checks for visible copy across the three question banks.

These catch concrete editorial defects. They do not claim to be a spellchecker
or reject technical English, intentional malformed-bracket exercises, or code.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTECTED = re.compile(r"```[\s\S]*?```|`[^`\n]*`|\\\[[\s\S]*?\\\]|\\\([^\n]*?\\\)")


def strings(value, language=None):
    if isinstance(value, str):
        yield language, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from strings(child, key if key in {"he", "en"} else language)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child, language)


def visible_copy():
    for name in ("example", "preparation"):
        for question in json.loads((ROOT / f"backend/seeds/questions/{name}_bank.json").read_bytes()):
            yield question["key"], question["translations"]
            yield question["key"], question["assets"].get("preparation_resource", {}).get("learner_material", {})
    for path in (ROOT / "apps/web/src/content").glob("fundamentals-*.json"):
        if path.name == "fundamentals-revisions.json":
            continue
        for card in json.loads(path.read_bytes()):
            yield card["id"], {field: card[field] for field in ("title", "prompt", "answer", "takeaway")}
    for question in json.loads((ROOT / "backend/seeds/duel_quiz.json").read_bytes())["questions"]:
        yield question["key"], {field: question[field] for field in ("prompt", "choices", "explanation")}


def test_no_literal_direction_escapes_or_accidental_repeated_assumptions():
    defects = re.compile(r"\\u(?:200[eEfF]|202[a-eA-E]|206[6-9])|\bexplicit\s+explicit\b", re.I)
    failures = []
    for key, fields in visible_copy():
        for _, value in strings(fields):
            prose = PROTECTED.sub("", value)
            if match := defects.search(prose):
                failures.append((key, prose[max(0, match.start() - 35):match.end() + 70]))
    assert not failures, failures


def test_english_prose_does_not_contain_untranslated_hebrew():
    failures = []
    for key, fields in visible_copy():
        for language, value in strings(fields):
            if language != "en":
                continue
            prose = PROTECTED.sub("", value)
            if match := re.search(r"[א-ת]", prose):
                failures.append((key, prose[max(0, match.start() - 35):match.end() + 70]))
    assert not failures, failures


def test_prose_spacing_preserves_named_functions_types_and_boolean_identifiers():
    bank = {question["key"]: question for question in json.loads(
        (ROOT / "backend/seeds/questions/preparation_bank.json").read_bytes()
    )}
    for language in ("he", "en"):
        random_prompt = bank["prep-uniform-random7-from-random5-rejection"]["translations"][language]["prompt"]
        assert "Random5" in random_prompt and "Random7" in random_prompt
        shuffle_prompt = bank["prep-random-permutation-fisher-yates"]["translations"][language]["prompt"]
        assert "Shuffle100" in shuffle_prompt
        reference = bank["prep-abstract-64-bit-word-matching-and-streak"]["translations"][language]["reference_solution"]
        assert "hit=(have0 && sample==ref0)||(have1 && sample==ref1)" in reference
    recursive = bank["prep-maximum-of-two-numbers-circuit"]["assets"]["preparation_resource"]["learner_material"]
    text = "\n".join(value for _, value in strings(recursive))
    assert "borrow0" in text and "borrow1" in text
    assert not re.search(r"\bborrow [01]\b", text)
