"""Preserve source decisions, current difficulty fingerprints and one revision per extension."""
import hashlib
import json
from pathlib import Path

from app.engine.catalog import load_catalog
from app.engine.question_difficulty import difficulty_fingerprint
from app.engine.solution_review import solution_review
from app.services.question_resources import learner_media
from tests.preparation_november15c_history import before_nov15c

ROOT=Path(__file__).resolve().parents[2]
BANK=ROOT/"interview_preparation"
SEEDS=ROOT/"backend/seeds"
MAP=(211,1,358,162,353,354,356,66,357,355)
NEW={f"PREP-{n}" for n in range(353,359)}
VARIANTS={"PREP-001","PREP-211"}


def read(path):
    return json.loads(path.read_bytes())


def test_ten_sources_keep_byte_hashes_and_semantic_identity():
    batch=read(BANK/"intakes/2026-11-15-batch10c-sources.json")
    archive={q["id"]:q for q in read(BANK/"questions.json")["questions"]}
    assert (batch["source_count"],batch["new_question_count"],batch["technical_extension_count"],
            batch["provenance_only_count"],batch["affected_question_count"]) == (10,6,2,2,10)
    for number,(source,ident) in enumerate(zip(batch["sources"],MAP,strict=True),1):
        ident=f"PREP-{ident:03}"
        assert source["question_ids"] == [ident]
        path=f"sources/2026-11-15-batch10c-{number:02}.png"
        assert source["archive_paths"] == [path]
        assert hashlib.sha256((BANK/path).read_bytes()).hexdigest() == source["sha256"]
        assert any(s["path"]==path for s in archive[ident]["sources"])
        assert set(source["reported_companies"]) <= set(archive[ident]["reported_companies"])


def test_one_revision_bilingual_material_hidden_sources_and_ratings():
    catalog=load_catalog(SEEDS)
    raw={q["key"]:q for q in read(SEEDS/"questions/preparation_bank.json")}
    ratings=read(SEEDS/"question_difficulty.json")
    selected={q.assets["preparation_id"]:q for q in catalog.questions.values()
              if q.assets.get("preparation_id") in NEW|VARIANTS}
    assert selected.keys()==NEW|VARIANTS
    for ident,q in selected.items():
        row=raw[q.key]
        prior=before_nov15c("compiled:"+q.key,row)
        assert q.version==(prior["version"]+1 if ident in VARIANTS else 1)
        assert solution_review(q).status=="pending_review"
        assert q.status=="trial" and not q.assets["assessment_ready"]
        rating=ratings[q.key]
        assert type(rating["difficulty"]) is int and 1<=rating["difficulty"]<=10
        assert rating["reason"].strip() and rating["content_sha256"]==difficulty_fingerprint(row)
        assert q.difficulty==rating["difficulty"]
        for lang in ("he","en"):
            assert q.text(lang).prompt and q.text(lang).reference_solution
            assert len(q.text(lang).hints)==3
            assert all(not m["source_path"].startswith("sources/")
                       for m in learner_media(q.assets["bank_media"],lang))
