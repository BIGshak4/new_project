"""Catalog expansion must preserve all existing learner-facing content identities."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps/web/src/content"
ORIGINAL = ("fundamentals-hardware.json", "fundamentals-code-logic.json")
ADDED = ("fundamentals-hardware-expansion.json", "fundamentals-reasoning-expansion.json",
         "fundamentals-code-expansion.json")
INTERVIEW_DERIVED = ("fundamentals-hardware-250.json", "fundamentals-reasoning-250.json",
                     "fundamentals-code-250.json")


def cards(names):
    return [card for name in names for card in json.loads((CONTENT / name).read_text(encoding="utf-8"))]


def test_all_120_original_cards_are_unchanged_including_ids_and_nested_content():
    original = cards(ORIGINAL)
    canonical = json.dumps(original, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert len(original) == 120
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "8e5c0fdfdb1a2dd1f0e85fb384e7ad454e1d8b3148da49761e8d68b9b919ea75"
    )


def test_250_unique_cards_with_rounded_topic_mix_and_distinct_bilingual_prompts():
    all_cards = cards(ORIGINAL + ADDED + INTERVIEW_DERIVED)
    assert len(all_cards) == len({card["id"] for card in all_cards}) == 250
    groups = Counter("hardware" if q["id"].startswith("quick-hw-") else
                     "reasoning" if q["topic"] == "reasoning" else "software" for q in all_cards)
    assert groups == {"hardware": 125, "reasoning": 88, "software": 37}
    for language in ("he", "en"):
        for field in ("title", "prompt"):
            texts = [card[field][language].strip().casefold() for card in all_cards]
            assert len(set(texts)) == 250


def test_each_added_card_has_its_actual_revision_in_both_runtime_manifests():
    web = json.loads((CONTENT / "fundamentals-revisions.json").read_text(encoding="utf-8"))
    backend = json.loads((ROOT / "backend/seeds/fundamentals_catalog.json").read_text(encoding="utf-8"))["questions"]
    assert len(web) == len(backend) == 400
    for card in cards(ADDED + INTERVIEW_DERIVED):
        canonical = json.dumps(card, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        revision = hashlib.sha256(canonical.encode()).hexdigest()
        assert web[card["id"]] == backend[card["id"]] == revision


def test_all_200_previous_cards_and_revisions_are_frozen():
    old = cards(ORIGINAL + ADDED)
    assert len(old) == 200
    canonical = json.dumps(old, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "f06254b7d4f316c4bae3fe323274be9604f77d9d06251a773def3eb8fa1b98c5"
    )


def test_50_new_cards_trace_to_real_interview_questions_and_have_no_review_claim():
    interview_ids = {q["id"] for q in json.loads((ROOT / "interview_preparation/questions.json").read_bytes())["questions"]}
    new = cards(INTERVIEW_DERIVED)
    assert len(new) == 50
    for card in new:
        assert card.get("interviewIds"), card["id"]
        assert set(card["interviewIds"]) <= interview_ids, card["id"]
        assert len(card["interviewIds"]) == len(set(card["interviewIds"]))
        assert "solution_review" not in card and "company" not in card
        for language in ("he", "en"):
            for field, limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
                text = card[field][language]
                assert text.strip() and len(text.split()) <= limit, (card["id"], field, language)
