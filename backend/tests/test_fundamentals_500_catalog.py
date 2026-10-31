"""500-card expansion preserves the exact prior400 and all2040 quiz records."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps/web/src/content"
SEEDS = ROOT / "backend/seeds"
FROZEN_SOURCES = {'fundamentals-code-250.json': '7bf15b8e095fd920596724a76db81b7dea7a794ae76c2f963563874f431b7470', 'fundamentals-code-400.json': 'a4320374fbc58b5a9b1f083eee832ef75dcbcf01325fd9c8305391fef34ee412', 'fundamentals-code-expansion.json': '16b2ff6a0e2071b0ec92dc526647d8ddd70fe49b2a6296ad223a26ae8c9d1823', 'fundamentals-code-logic.json': 'd8012fe97385ec924a0bd31c07bb6fd20a64eb3f39912572fc512f6aa1ad5e1f', 'fundamentals-hardware-250.json': 'd9ea4e135e6ed0e2225c4538228daa2ec59cf0bee8f662057de350ac7f01da8d', 'fundamentals-hardware-400.json': '042673ec146d81f190e256b1b8cf5ee1a7d535645fd4480eed03c684b942fdce', 'fundamentals-hardware-expansion.json': 'be5cc9b500f314821accc08172408279572773c50620f2b86c0fcdc9940b4f60', 'fundamentals-hardware.json': '3d942668f98ce6065d09727f1509c483124a61b46c94ddb3a09407cc67cbe8d0', 'fundamentals-reasoning-250.json': 'ac1bb8d8f4a06f3a4e2342f87941d0d7b34e45b8b86d2d8c664a5fb20b6229df', 'fundamentals-reasoning-400.json': '9e0915e1c5a80afda9f456818fc7b6a803c4fd63fef47c8d2d0b71002915e5b5', 'fundamentals-reasoning-expansion.json': '507a827ec0e1719209aac9da6f7ed483696bbda454caad8ae2412e1d90cc4e2a'}
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
    assert digest(previous) == "836a2274173b0851819183ffe1076b3018e789bc3c69b87e1d084413fa087067"


def test_all2040_previous_quiz_objects_and1950_release_entries_are_frozen():
    quiz = read(SEEDS / "duel_quiz.json")["questions"]
    previous = sorted([q for q in quiz if not q.get("source_key") or prior(q["source_key"])], key=lambda q: q["key"])
    assert len(previous) == 2040
    assert digest(previous) == "d5658c38b6abbad3a0354993738e751e5a376a1a8cbbbf15efabf38a4e4067af"
    manifest = read(SEEDS / "duel_quiz_batches/release-manifest.json")
    entries = [row for row in manifest["questions"] if prior(row["key"].rsplit("-v", 1)[0])]
    assert len(entries) == 1950
    assert digest(entries) == "5a7ee21ddf77b5e0a00fb7f43bdae2b6b56ab02e4435eb9acdfa7c4899796fcc"
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
