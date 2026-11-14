"""The 700-card release preserves prior learning records and adds 200 linked drills."""

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps/web/src/content"
SEEDS = ROOT / "backend/seeds"
DOMAINS = ("hardware", "reasoning", "code")


def read(path):
    return json.loads(path.read_bytes())


def digest(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def prior(key):
    return int(key.rsplit("-", 1)[1]) <= 250


def test_prior500_revisions_and2540_quiz_records_are_unchanged():
    web = read(CONTENT / "fundamentals-revisions.json")
    backend = read(SEEDS / "fundamentals_catalog.json")["questions"]
    assert web == backend and len(web) == 700
    old = {key: value for key, value in web.items() if prior(key)}
    assert len(old) == 500
    assert digest(old) == "4ea925755eff42b2b404de5b1b003317638830d5d6358e9930e35f3291258c1a"
    quiz = read(SEEDS / "duel_quiz.json")["questions"]
    previous = sorted(
        [q for q in quiz if not q.get("source_key") or prior(q["source_key"])], key=lambda q: q["key"]
    )
    assert len(previous) == 2540
    assert digest(previous) == "2c0ce24b2f1fafdd159bd109ebaf29e5a5cde977b1040d77b966a333adf3e1f6"
    entries = read(SEEDS / "duel_quiz_batches/release-manifest.json")["questions"]
    old_entries = [q for q in entries if prior(q["key"].rsplit("-v", 1)[0])]
    assert len(old_entries) == 2450
    assert digest(old_entries) == "a962bf00f3f880801bfce9336883b424c462d2bef5658d62579bbe16341cad87"


def test_200_new_cards_are_concise_bilingual_linked_and_distinct():
    new = [q for domain in DOMAINS for q in read(CONTENT / f"fundamentals-{domain}-700.json")]
    all_cards = [
        q
        for path in CONTENT.glob("fundamentals-*.json")
        if isinstance(rows := read(path), list)
        for q in rows
    ]
    assert len(new) == 200 and len(all_cards) == 700
    assert {q["id"] for q in new} == {f"quick-hw-{n}" for n in range(251, 351)} | {
        f"quick-sw-{n}" for n in range(251, 351)
    }
    assert Counter(
        "hardware"
        if q["id"].startswith("quick-hw-")
        else "reasoning"
        if q["topic"] == "reasoning"
        else "code"
        for q in all_cards
    ) == {"hardware": 350, "reasoning": 245, "code": 105}
    prep = {q["id"] for q in read(ROOT / "interview_preparation/questions.json")["questions"]}
    for lang in ("he", "en"):
        for field in ("title", "prompt"):
            assert len({q[field][lang].strip().casefold() for q in all_cards}) == 700
    for q in new:
        assert q["interviewIds"] and set(q["interviewIds"]) <= prep
        assert "company" not in q and "solution_review" not in q
        for field, cap in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
            assert set(q[field]) == {"he", "en"}
            for lang, value in q[field].items():
                assert value == value.strip() and 0 < len(value.split()) <= cap, (q["id"], field, lang)
                assert not any(c in value for c in ("\ufffd", "\ufeff", "\x00"))
                if lang == "en":
                    assert not any("\u0590" <= c <= "\u05ff" for c in value), q["id"]
        if "code" in q:
            assert len(q["code"]["text"].splitlines()) <= 5


def test_1000_new_variants_have_hash_bound_release_and_backend_difficulty():
    quiz = read(SEEDS / "duel_quiz.json")["questions"]
    additions = [q for q in quiz if q.get("source_key") and not prior(q["source_key"])]
    assert len(quiz) == 3540 and len(additions) == 1000
    assert sum(q["status"] == "approved" for q in quiz) == 3500
    counts = Counter(q["source_key"] for q in additions)
    assert len(counts) == 200 and set(counts.values()) == {5}
    checks = {
        q["key"]: q for domain in DOMAINS for q in read(SEEDS / f"duel_quiz_batches/{domain}_700.checks.json")
    }
    assert set(checks) == {q["key"] for q in additions}
    for q in additions:
        assert q["release_approval"]["on"] == "2026-11-12"
        assert q["release_approval"]["professional_review"] == "pending"
        assert 1 <= checks[q["key"]]["difficulty"] <= 10
        assert checks[q["key"]]["difficulty_rationale"].strip()
