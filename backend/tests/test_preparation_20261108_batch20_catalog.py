"""Twenty-source intake: append-only content, exact difficulty and private diagrams."""
from __future__ import annotations

import copy
import hashlib
import json
import uuid
from pathlib import Path

import pytest

from app.engine.catalog import load_catalog
from app.engine.question_difficulty import difficulty_fingerprint
from app.engine.solution_review import solution_review
from app.repo.questions import LoadedQuestion, detail, summary
from app.services.question_resources import learner_media
from tests.preparation_history import (
    BATCH1108B20_BASELINE,
    assert_pre_batch1108b20_archive,
    assert_pre_batch1108b20_assets,
    assert_pre_batch1108b20_localization,
    digest,
)
from tests.preparation_november8_batch20_history import before_batch1108b20_compiled
from tests.copy_november12_history import before_current_copy, before_current_fundamentals_manifest

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds"
NEW = {f"PREP-{n}" for n in range(303, 312)}
VARIANTS = {"PREP-018", "PREP-022", "PREP-035", "PREP-053", "PREP-132", "PREP-299"}
SOURCE_ONLY = {"PREP-036", "PREP-037", "PREP-058", "PREP-085", "PREP-096"}
MAP = (36,303,304,305,85,132,37,306,307,58,22,308,309,53,18,35,310,299,311,96)


def read(path):
    return json.loads(path.read_bytes())


def test_twenty_originals_and_exact_canonical_mapping():
    manifest = read(BANK / "intakes/2026-11-08-batch20-sources.json")
    records = {q["id"]: q for q in read(BANK / "questions.json")["questions"]}
    assert manifest["screenshot_count"] == manifest["question_source_count"] == 20
    assert (manifest["new_question_count"], manifest["technical_extension_count"], manifest["provenance_only_count"]) == (9,6,5)
    for item, number in zip(manifest["sources"], MAP, strict=True):
        ident = f"PREP-{number:03}"
        assert item["question_ids"] == [ident]
        assert item["sha256"] == BATCH1108B20_BASELINE["batch1108b20_source_sha256"][str(item["screenshot"])]
        path = item["archive_paths"][0]
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == item["sha256"]
        assert set(item["reported_companies"]) <= set(records[ident]["reported_companies"])
        assert any(s["path"] == path for s in records[ident]["sources"])
        assert set(item["source_tags"]) <= set(records[ident]["source_tags"])


def test_all_301_previous_records_media_translations_and_ratings_remain_bound():
    archive = read(BANK / "questions.json")
    assert len(archive["questions"]) == archive["question_count"] == 310
    assert {q["id"] for q in archive["questions"]} - BATCH1108B20_BASELINE["records"].keys() == NEW
    assert_pre_batch1108b20_archive(archive)
    assert_pre_batch1108b20_assets(read(SEEDS / "preparation_uploads.json")["files"])
    localized = {}
    for path in (SEEDS / "preparation_localization").glob("*.json"):
        values = read(path)
        assert not localized.keys() & values.keys()
        localized.update(values)
    assert localized.keys() == {q["id"] for q in archive["questions"]}
    assert_pre_batch1108b20_localization(localized)
    for q in read(SEEDS / "questions/preparation_bank.json"):
        if q["assets"]["preparation_id"] in BATCH1108B20_BASELINE["records"]:
            before_batch1108b20_compiled(q)


def test_current_difficulties_reach_engine_without_exposing_scores_to_learners():
    ratings = read(SEEDS / "question_difficulty.json")
    catalog = load_catalog(SEEDS)
    assert len(catalog.questions) == len(ratings) == 340
    selected = {q.assets.get("preparation_id"): q for q in catalog.questions.values()
                if q.assets.get("preparation_id") in NEW | VARIANTS | SOURCE_ONLY}
    assert len(selected) == 20
    for ident, q in selected.items():
        entry = ratings[q.key]
        assert type(entry["difficulty"]) is int and 1 <= entry["difficulty"] <= 10 and entry["reason"].strip()
        assert q.difficulty == entry["difficulty"] and q.assets["difficulty_status"] == "rated"
        assert difficulty_fingerprint(q.model_dump(mode="json")) == entry["content_sha256"]
        loaded = LoadedQuestion(id=uuid.uuid4(), question=q, version=q.version)
        for language in ("he", "en"):
            assert "difficulty" not in summary(loaded, language).model_dump()
            assert "difficulty" not in detail(loaded, language).model_dump()
        if ident in NEW | VARIANTS:
            assert q.status == "trial" and not q.assets["assessment_ready"]
            assert solution_review(q).status == "pending_review"
    old = BATCH1108B20_BASELINE["difficulty_ratings"]
    revised_keys = {selected[ident].key for ident in VARIANTS | SOURCE_ONLY}
    compiled = {q["key"]: q for name in ("example", "preparation")
                for q in read(SEEDS / f"questions/{name}_bank.json")}
    for key, entry in old.items():
        if key in revised_keys:
            continue
        # Copy changes rebind the fingerprint while preserving the reviewed score
        # and rationale. The exact reverse projection still proves the old hash.
        kind = "example" if key.startswith("example-") else "preparation"
        previous = before_current_copy(kind, f"compiled:{key}", compiled[key])
        assert difficulty_fingerprint(previous) == entry["content_sha256"]
        assert {k: v for k, v in ratings[key].items() if k != "content_sha256"} == {
            k: v for k, v in entry.items() if k != "content_sha256"}
    for ident in SOURCE_ONLY:
        key = selected[ident].key
        assert ratings[key]["difficulty"] == old[key]["difficulty"]
        assert ratings[key]["reason"] == old[key]["reason"]


def test_bilingual_material_three_hints_and_diagrams_respect_reveal_boundaries():
    catalog = load_catalog(SEEDS)
    for q in catalog.questions.values():
        ident = q.assets.get("preparation_id")
        if ident not in NEW | VARIANTS | SOURCE_ONLY:
            continue
        for language in ("he", "en"):
            text = q.text(language)
            assert text.prompt and text.reference_solution and len(set(text.hints)) == 3
            media = learner_media(q.assets["bank_media"], language)
            assert all(not m["source_path"].startswith("sources/") for m in media)
            assert any(m["kind"] == "image" for m in media), (ident, language)
        if ident in NEW | VARIANTS:
            for key, pair in q.assets["preparation_resource"]["learner_material"].items():
                assert set(pair) == {"he", "en"} and pair["he"] and pair["en"], (ident, key)
                assert not any("\u05d0" <= c <= "\u05ea" for c in json.dumps(pair["en"], ensure_ascii=False)), (ident, key)


def test_original_literal_threshold_and_sine_ambiguity_are_preserved():
    manifest = read(BANK / "intakes/2026-11-08-batch20-sources.json")
    assert "שני שלישים" in manifest["sources"][8]["original_prompt"]
    assert "Sin(2pi*n*T)" in manifest["sources"][17]["original_prompt"]
    raw = {q["id"]: q for q in read(BANK / "questions.json")["questions"]}
    for ident in SOURCE_ONLY:
        previous = BATCH1108B20_BASELINE["records"][ident]["projection"]
        assert raw[ident]["version"] == previous["version"]


def test_fundamentals_quiz_and_human_registry_unchanged():
    baseline = BATCH1108B20_BASELINE
    for name, expected in baseline["short_card_source_sha256"].items():
        assert digest(before_current_copy("fundamentals", name,
                                          read(ROOT / "apps/web/src/content" / name))) == expected
    for name, key in [("fundamentals_catalog.json", "fundamentals_catalog_sha256"),
                      ("duel_quiz.json", "quiz_bank_sha256"),
                      ("solution_review_attestations.json", "review_registry_canonical_sha256")]:
        actual = read(SEEDS / name)
        if name == "fundamentals_catalog.json":
            actual = before_current_fundamentals_manifest(actual)
        elif name == "duel_quiz.json":
            actual = before_current_copy("quiz", name, actual)
        assert digest(actual) == baseline[key]


def test_native_proof_is_bound_to_sources_and_confirmed_running_session_policy():
    proof = read(BANK / "checks/batch1108b20-native-verification.json")
    assert proof["result"] == "passed" and proof["command_exit_code"] == 0
    assert proof["rtl_check_total"] == 66134
    assert proof["c_shuffle"]["checks"] == 6665 and proof["java_stack"]["checks"] == 12003
    assert proof["environment"]["test_network_policy"] == "deny-all"
    assert proof["environment"]["session_stopped"] and not proof["environment"]["persistent"]
    assert proof["running_session_policy_verified"]["mode"] == "deny-all"
    assert proof["running_session_policy_verified"]["confirmed_again_after_stop"]
    for path, expected in proof["source_sha256"].items():
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == expected


@pytest.mark.parametrize("mutation", ["title", "hint", "prompt", "version", "media", "digest", "difficulty"])
def test_historical_projection_rejects_unauthorized_mutations(mutation):
    q = copy.deepcopy(next(q for q in read(SEEDS / "questions/preparation_bank.json")
                           if q["assets"]["preparation_id"] == "PREP-022"))
    if mutation == "title":
        q["translations"]["en"]["title"] = "changed"
    elif mutation == "hint":
        q["translations"]["en"]["hints"][0] = "changed"
    elif mutation == "prompt":
        q["translations"]["en"]["prompt"] = "changed"
    elif mutation == "version":
        q["version"] += 1
    elif mutation == "difficulty":
        q["difficulty"] = 1
    elif mutation == "media":
        path = next(m["path"] for m in q["assets"]["bank_media"] if "1108b20" not in m["source_path"]
                    and not m["source_path"].startswith("sources/2026-11-08-batch20"))
        next(m for m in q["assets"]["bank_media"] if m["path"] == path)["caption"] = "changed"
    else:
        q["assets"]["source_sha256"] = "0" * 64
    with pytest.raises(AssertionError):
        before_batch1108b20_compiled(q)
