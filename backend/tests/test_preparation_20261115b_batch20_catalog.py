"""Preserve merged source identities, exact revision advances, and original-image privacy."""
import hashlib
import json
from pathlib import Path

from app.engine.catalog import load_catalog
from app.engine.question_difficulty import difficulty_fingerprint
from app.engine.solution_review import solution_review
from app.services.question_resources import learner_media
from tests.preparation_november15b_history import before_nov15b
from tests.preparation_november15c_history import before_nov15c

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds"
MAP = (346,64,176,65,347,349,30,205,65,182,350,110,64,351,352,58,44,348,247,176)
NEW = {f"PREP-{n}" for n in range(346,353)}
VARIANTS = {"PREP-044","PREP-058","PREP-110","PREP-176","PREP-182","PREP-205"}


def read(path):
    return json.loads(path.read_bytes())


def test_all_twenty_sources_keep_semantic_matches_and_private_originals():
    manifest = read(BANK / "intakes/2026-11-15-batch20b-sources.json")
    archive = {q["id"]: q for q in read(BANK / "questions.json")["questions"]}
    assert manifest["source_count"] == len(manifest["sources"]) == len(MAP)
    assert (manifest["new_question_count"],manifest["technical_extension_count"],
            manifest["provenance_only_count"],manifest["affected_question_count"]) == (7,6,4,17)
    for number,(source,ident) in enumerate(zip(manifest["sources"],MAP,strict=True),1):
        ident=f"PREP-{ident:03}"
        assert source["question_ids"] == [ident]
        path=f"sources/2026-11-15-batch20b-{number:02}.png"
        assert source["archive_paths"] == [path]
        assert hashlib.sha256((BANK/path).read_bytes()).hexdigest() == source["sha256"]
        assert any(s["path"] == path for s in archive[ident]["sources"])
        assert set(source["reported_companies"]) <= set(archive[ident]["reported_companies"])
        assert set(source["source_tags"]) <= set(archive[ident]["source_tags"])


def test_exact_single_revision_bilingual_content_difficulty_and_media_gates():
    catalog=load_catalog(SEEDS)
    compiled={q["key"]:q for q in read(SEEDS/"questions/preparation_bank.json")}
    ratings=read(SEEDS/"question_difficulty.json")
    selected={q.assets["preparation_id"]:q for q in catalog.questions.values()
              if q.assets.get("preparation_id") in NEW|VARIANTS}
    assert selected.keys() == NEW|VARIANTS
    for ident,question in selected.items():
        q=compiled[question.key]
        previous=before_nov15b("compiled:"+question.key,q)
        at_intake=before_nov15c("compiled:"+question.key,q)
        assert q["version"] == question.version
        assert at_intake["version"] == (previous["version"]+1 if ident in VARIANTS else 1)
        rating=ratings[question.key]
        assert type(rating["difficulty"]) is int and 1 <= rating["difficulty"] <= 10
        assert rating["reason"].strip() and rating["content_sha256"] == difficulty_fingerprint(q)
        assert question.difficulty == rating["difficulty"]
        assert question.status == "trial" and not question.assets["assessment_ready"]
        assert solution_review(question).status == "pending_review"
        for lang in ("he","en"):
            assert len(question.text(lang).hints) == 3
            assert question.text(lang).prompt and question.text(lang).reference_solution
            assert all(not m["source_path"].startswith("sources/")
                       for m in learner_media(question.assets["bank_media"],lang))
