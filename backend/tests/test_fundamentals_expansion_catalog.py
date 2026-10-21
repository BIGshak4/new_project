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


def cards(names):
    return [card for name in names for card in json.loads((CONTENT / name).read_text(encoding="utf-8"))]


def test_all_120_original_cards_are_unchanged_including_ids_and_nested_content():
    original = cards(ORIGINAL)
    canonical = json.dumps(original, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert len(original) == 120
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "8e5c0fdfdb1a2dd1f0e85fb384e7ad454e1d8b3148da49761e8d68b9b919ea75"
    )


def test_200_unique_cards_with_exact_requested_topic_mix_and_distinct_bilingual_prompts():
    all_cards = cards(ORIGINAL + ADDED)
    assert len(all_cards) == len({card["id"] for card in all_cards}) == 200
    groups = Counter("hardware" if q["id"].startswith("quick-hw-") else
                     "reasoning" if q["topic"] == "reasoning" else "software" for q in all_cards)
    assert groups == {"hardware": 100, "reasoning": 70, "software": 30}
    for language in ("he", "en"):
        for field in ("title", "prompt"):
            texts = [card[field][language].strip().casefold() for card in all_cards]
            assert len(set(texts)) == 200


def test_each_added_card_has_its_actual_revision_in_both_runtime_manifests():
    web = json.loads((CONTENT / "fundamentals-revisions.json").read_text(encoding="utf-8"))
    backend = json.loads((ROOT / "backend/seeds/fundamentals_catalog.json").read_text(encoding="utf-8"))["questions"]
    assert len(web) == len(backend) == 200
    for card in cards(ADDED):
        canonical = json.dumps(card, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        revision = hashlib.sha256(canonical.encode()).hexdigest()
        assert web[card["id"]] == backend[card["id"]] == revision
