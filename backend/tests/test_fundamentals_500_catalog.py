"""500-card expansion preserves the exact prior400 and all2040 quiz records."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps/web/src/content"
SEEDS = ROOT / "backend/seeds"
# 2026-11-04: authorized learner-copy baseline; all identity, grading and source-history assertions remain in place.
FROZEN_SOURCES = {'fundamentals-code-250.json': '7bf15b8e095fd920596724a76db81b7dea7a794ae76c2f963563874f431b7470', 'fundamentals-code-400.json': 'a4320374fbc58b5a9b1f083eee832ef75dcbcf01325fd9c8305391fef34ee412', 'fundamentals-code-expansion.json': '16b2ff6a0e2071b0ec92dc526647d8ddd70fe49b2a6296ad223a26ae8c9d1823', 'fundamentals-code-logic.json': 'd8012fe97385ec924a0bd31c07bb6fd20a64eb3f39912572fc512f6aa1ad5e1f', 'fundamentals-hardware-250.json': 'c1e945aea20276a5f05b6be040c043501e6bd4e774ff2db46913f13a133d3634', 'fundamentals-hardware-400.json': '042673ec146d81f190e256b1b8cf5ee1a7d535645fd4480eed03c684b942fdce', 'fundamentals-hardware-expansion.json': 'ee93ad7796923ee32c90daaca7626c791b29b60aad8e91f1502fccc36f6e35c0', 'fundamentals-hardware.json': '5f147cd447817ea020f1adf9bfe665d396e2cb2b684f07841d6b70c015208289', 'fundamentals-reasoning-250.json': 'ac1bb8d8f4a06f3a4e2342f87941d0d7b34e45b8b86d2d8c664a5fb20b6229df', 'fundamentals-reasoning-400.json': '9e0915e1c5a80afda9f456818fc7b6a803c4fd63fef47c8d2d0b71002915e5b5', 'fundamentals-reasoning-expansion.json': '507a827ec0e1719209aac9da6f7ed483696bbda454caad8ae2412e1d90cc4e2a'}
NEW_FILES = [f"fundamentals-{domain}-500.json" for domain in ("hardware", "reasoning", "code")]


def read(path):
    return json.loads(path.read_bytes())


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def prior(key):
    return int(key.rsplit("-", 1)[1]) <= 200


def test_prior400_bytes_ids_and_revision_hashes_are_frozen():
    for name, expected in FROZEN_SOURCES.items():
        assert hashlib.sha256((CONTENT / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() == expected, name
    web = read(CONTENT / "fundamentals-revisions.json")
    backend = read(SEEDS / "fundamentals_catalog.json")["questions"]
    assert web == backend and len(web) == 500
    previous = {key: value for key, value in web.items() if prior(key)}
    assert len(previous) == 400
    assert digest(previous) == "6c29e82c63f25aeea21694435d3acdb55e6b384a1a33fd0cea4fd5cde2e0e201"


def test_all2040_previous_quiz_objects_and1950_release_entries_are_frozen():
    quiz = read(SEEDS / "duel_quiz.json")["questions"]
    previous = sorted([q for q in quiz if not q.get("source_key") or prior(q["source_key"])], key=lambda q: q["key"])
    assert len(previous) == 2040
    assert digest(previous) == "49d2826adfb07c0a20ab999821dbdce40b239c4f274eed036aac48afd998b776"
    manifest = read(SEEDS / "duel_quiz_batches/release-manifest.json")
    entries = [row for row in manifest["questions"] if prior(row["key"].rsplit("-v", 1)[0])]
    assert len(entries) == 1950
    assert digest(entries) == "15c66237482dc8b94c9d4d5a65ea1344a562a4edd626a125fab2c2a227571401"
    additions = [q for q in quiz if q.get("source_key") and not prior(q["source_key"])]
    assert len(quiz) == 2540 and len(additions) == 500
    assert sum(q["status"] == "approved" for q in quiz) == 2500
    assert all(q["release_approval"]["on"] == "2026-10-31" and
               q["release_approval"]["professional_review"] == "pending" for q in additions)


def test_100_short_additions_are_concise_bilingual_linked_and_distinct():
    old = [q for name in FROZEN_SOURCES for q in read(CONTENT / name)]
    new = [q for name in NEW_FILES for q in read(CONTENT / name)]
    assert len(new) == 100
    assert {q["id"] for q in new} == {f"quick-hw-{n}" for n in range(201, 251)} | {f"quick-sw-{n}" for n in range(201, 251)}
    assert Counter("hardware" if q["id"].startswith("quick-hw-") else "reasoning" if q["topic"] == "reasoning" else "code" for q in old + new) == {"hardware": 250, "reasoning": 175, "code": 75}
    prep = {q["id"] for q in read(ROOT / "interview_preparation/questions.json")["questions"]}
    for lang in ("he", "en"):
        for field in ("title", "prompt"):
            assert len({q[field][lang].strip().casefold() for q in old + new}) == 500
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
