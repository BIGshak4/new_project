"""Publication and backward compatibility for the 800-card game bank."""

import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps/web/src/content"
SEEDS = ROOT / "backend/seeds"
BATCHES = SEEDS / "duel_quiz_batches"
DOMAINS = {"hardware": 50, "reasoning": 35, "code": 15}
NEW = {f"quick-{domain}-{i}" for domain in ("hw", "sw") for i in range(351, 401)}


def read(path):
    return json.loads(path.read_bytes())


def digest(obj):
    data = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def test_preexisting_revisions_games_and_release_entries_are_preserved():
    registry = read(SEEDS / "fundamentals_catalog.json")["questions"]
    assert registry == read(CONTENT / "fundamentals-revisions.json")
    assert len(registry) == 800 and registry.keys() >= NEW
    assert digest({k: v for k, v in registry.items() if k not in NEW}) == (
        "580187c03c50ddbf4af98bf9e640a763de0abc9b7744f53cc64624b856c78970"
    )
    games = read(SEEDS / "duel_quiz.json")["questions"]
    assert digest([q for q in games if q.get("source_key") not in NEW]) == (
        "d87d5e439c8590df830daa88bc885509c97a2818754fe704817831148270486b"
    )
    manifest = read(BATCHES / "release-manifest.json")["questions"]
    assert digest([q for q in manifest if q["key"].rsplit("-v", 1)[0] not in NEW]) == (
        "996f5db90ce6bea6f5346511b703674e20d6e7929c05974f004a5b810dac86a1"
    )


@pytest.mark.parametrize("domain,count", DOMAINS.items())
def test_each_addition_links_to_a_real_interview_and_five_playable_variants(domain, count):
    interviews = {q["id"] for q in read(ROOT / "interview_preparation/questions.json")["questions"]}
    cards = read(CONTENT / f"fundamentals-{domain}-800.json")
    assert len(cards) == count
    for card in cards:
        assert card["id"] in NEW and card["interviewIds"] and set(card["interviewIds"]) <= interviews
        for field, limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
            assert set(card[field]) == {"he", "en"}
            assert all(0 < len(value.split()) <= limit for value in card[field].values())
    keys = {c["id"] for c in cards}
    games = [q for q in read(SEEDS / "duel_quiz.json")["questions"] if q.get("source_key") in keys]
    assert Counter(q["source_key"] for q in games) == {key: 5 for key in keys}
    checks = {q["key"]: q for q in read(BATCHES / f"{domain}_800.checks.json")}
    assert checks.keys() == {q["key"] for q in games}
    for game in games:
        assert game["status"] == "approved"
        assert game["release_approval"]["on"] == "2026-11-18"
        assert game["release_approval"]["professional_review"] == "pending"
        evidence = checks[game["key"]]
        assert 1 <= evidence["difficulty"] <= 10 and evidence["difficulty_rationale"]


def test_displayed_python_snippets_match_their_game_cases():
    cards = read(CONTENT / "fundamentals-code-800.json")
    checks = read(BATCHES / "code_800.checks.json")
    for card in cards:
        if "code" not in card:
            continue
        namespace = {}
        exec(card["code"]["text"], namespace)
        (function,) = [value for value in namespace.values() if callable(value)]
        for case in checks:
            if case["task"] == card["id"]:
                assert function(*case["inputs"]) == case["expected"]
