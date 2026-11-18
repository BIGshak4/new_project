"""Trace mixed screenshots, deduplication, chosen circuit assumptions and hidden media."""
import hashlib
import json
from pathlib import Path

from app.engine.question_difficulty import difficulty_fingerprint
from app.engine.catalog import load_catalog
from app.engine.solution_review import solution_review
from app.services.question_resources import learner_media
from tests.preparation_november15_history import before_nov15
from tests.preparation_november15b_history import before_nov15b

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds"
MAP = ((338, 342), (339,), (330,), (331,), (332,), (27,), (340,), (333,),
       (334,), (335,), (243,), (336,), (343,), (216,), (344,), (337,),
       (243,), (341,), (345,), (30,))
NEW = {f"PREP-{n}" for n in range(330, 346)}
VARIANTS = {"PREP-030", "PREP-216", "PREP-243"}


def read(path):
    return json.loads(path.read_bytes())


def test_twenty_archived_sources_preserve_split_and_merged_identities():
    manifest = read(BANK / "intakes/2026-11-15-batch20-sources.json")
    archived = {r["id"]: r for r in read(BANK / "questions.json")["questions"]}
    assert (manifest["new_question_count"], manifest["technical_extension_count"],
            manifest["provenance_only_count"], manifest["affected_question_count"]) == (16, 3, 1, 20)
    assert manifest["source_count"] == len(manifest["sources"]) == len(MAP) == 20
    for number, (source, numbers) in enumerate(zip(manifest["sources"], MAP, strict=True), 1):
        assert source["question_ids"] == [f"PREP-{n:03}" for n in numbers]
        assert source["screenshot"] == number and source["original_prompt"].strip()
        path = f"sources/2026-11-15-batch20-{number:02}.png"
        assert source["archive_paths"] == [path]
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == source["sha256"]
        for ident in source["question_ids"]:
            q = archived[ident]
            assert any(s.get("path") == path for s in q["sources"])
            assert set(source["reported_companies"]) <= set(q["reported_companies"])
            assert set(source["source_tags"]) <= set(q["source_tags"])
    assert archived["PREP-343"]["reported_companies"] == []
    # The PMC-Sierra label is a tag in the supplied screenshot.
    assert not manifest["sources"][5]["reported_companies"]


def test_complete_bilingual_difficulty_and_reveal_boundaries_follow_current_content():
    catalog = load_catalog(SEEDS)
    selected = {q.assets["preparation_id"]: q for q in catalog.questions.values()
                if q.assets.get("preparation_id") in NEW | VARIANTS}
    assert selected.keys() == NEW | VARIANTS
    ratings = read(SEEDS / "question_difficulty.json")
    compiled = {q["key"]: q for q in read(SEEDS / "questions/preparation_bank.json")}
    for ident, question in selected.items():
        q = question.model_dump(mode="json")
        current = compiled[q["key"]]
        history_key = "compiled:" + q["key"]
        at_intake = before_nov15b(history_key, current)
        assert q["version"] == current["version"]
        if ident in VARIANTS:
            prior = before_nov15(history_key, current)
            assert at_intake["version"] == prior["version"] + 1
        else:
            assert at_intake["version"] == 1
        r = ratings[q["key"]]
        assert type(r["difficulty"]) is int and 1 <= r["difficulty"] <= 10
        assert r["reason"].strip() and r["content_sha256"] == difficulty_fingerprint(q)
        assert q["difficulty"] == r["difficulty"] and q["assets"]["difficulty_status"] == "rated"
        assert q["status"] == "trial" and not q["assets"]["assessment_ready"]
        assert solution_review(question).status == "pending_review"
        for language in ("he", "en"):
            assert len(q["translations"][language]["hints"]) == 3
            material = q["assets"]["preparation_resource"]["learner_material"]
            assert material and all(pair[language] for pair in material.values())
            exposed = learner_media(q["assets"]["bank_media"], language)
            assert all(not m["source_path"].startswith("sources/") for m in exposed)
            assert q["translations"][language]["prompt"] and q["translations"][language]["reference_solution"]
            if ident in NEW:
                assert "solution_review" not in q["assets"]
