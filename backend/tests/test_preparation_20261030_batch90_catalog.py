"""Permanent contracts for twenty supplied sources and ten new study questions.

All service checks are in-memory. The seventeen model checks are finite exact
software/numerical oracles; no live learner writes or HDL compilation occur.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import uuid
from pathlib import Path

import pytest

from app.api.errors import ApiError
from app.engine import bank
from app.engine.catalog import load_catalog
from app.engine.solution_review import solution_review
from app.repo.questions import LoadedQuestion, summary
from app.services import question_resources
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.preparation_history import (
    BASELINE,
    BATCH110_BASELINE,
    assert_pre_batch90_archive,
    assert_pre_batch90_assets,
    assert_pre_batch110_assets,
    digest,
)
from tests.test_practice_hardening import scripted

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds"
NEW_IDS = {f"PREP-{number}" for number in range(178, 188)}
VARIANT_IDS = {"PREP-016", "PREP-064", "PREP-072", "PREP-076", "PREP-078", "PREP-095", "PREP-122"}
SOURCE_ONLY_IDS = {"PREP-059", "PREP-066"}
AFFECTED_IDS = NEW_IDS | VARIANT_IDS | SOURCE_ONLY_IDS
SOURCE_MAP = dict(enumerate((178, 179, 180, 66, 16, 122, 181, 182, 183, 64,
                             184, 76, 95, 185, 72, 16, 78, 186, 187, 59), 1))


def read(path):
    return json.loads(path.read_bytes())


def load_python(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def test_twenty_sources_keep_the_exact_original_bytes_and_identity_mapping():
    intake = read(BANK / "intakes/2026-10-30-batch90-sources.json")
    archive = {question["id"]: question for question in read(BANK / "questions.json")["questions"]}
    assert intake["screenshot_count"] == intake["question_source_count"] == len(intake["sources"]) == 20
    assert {source["screenshot"] for source in intake["sources"]} == set(SOURCE_MAP)
    for source in intake["sources"]:
        number = source["screenshot"]
        ident = f"PREP-{SOURCE_MAP[number]:03d}"
        path = f"sources/2026-10-30-batch90-{number:02d}.png"
        assert source["archive_paths"] == [path] and source["question_ids"] == [ident]
        assert source["original_prompt"].strip()
        assert source["sha256"] == BASELINE["batch90_source_sha256"][str(number)]
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == source["sha256"]
        question = archive[ident]
        assert any(item.get("path") == path for item in question["sources"])
        assert set(source["source_tags"]) <= set(question["source_tags"])
        assert set(source["reported_companies"]) <= set(question["reported_companies"])
        expected = ("new_manual_question" if ident in NEW_IDS else "existing_question_source_and_variant"
                    if ident in VARIANT_IDS else "additional_source_existing_question")
        assert source["decision"] == expected
    assert len(AFFECTED_IDS) == 19
    assert sum(f"PREP-{number:03d}" in VARIANT_IDS for number in SOURCE_MAP.values()) == 8


def test_authorized_extensions_preserve_all_176_original_records_and_921_assets(catalog):
    archive = read(BANK / "questions.json")
    assert len(archive["questions"]) == 197 and len(catalog.questions) == 227
    previous_ids = {question["id"] for question in archive["questions"] if int(question["id"].split("-")[1]) <= 187}
    assert previous_ids - set(BASELINE["records"]) == NEW_IDS
    assert_pre_batch90_archive(archive)
    assert_pre_batch90_assets(read(SEEDS / "preparation_uploads.json")["files"])
    # These three explicit existing aliases remain the only collapsed families.
    module = (ROOT / "apps/web/src/lib/question-families.ts").read_text("utf-8")
    pairs = re.findall(r'^\s*"([^"]+)":\s*"([^"]+)",', module, re.MULTILINE)
    aliases = dict(pairs)
    assert aliases == {
        "example-power-of-two-check": "prep-power-of-two-check",
        "example-merge-measurement-streams": "prep-merge-two-sorted-arrays",
        "example-overlapping-sequence-1011": "prep-detect-overlapping-1011-stream",
    }
    assert set(aliases) | set(aliases.values()) <= catalog.questions.keys()
    assert len({aliases.get(key, key) for key in catalog.questions}) == 224


def test_all_new_questions_and_extensions_remain_bilingual_proposed_unrated_and_gated(catalog):
    selected = {q.assets.get("preparation_id"): q for q in catalog.questions.values()
                if q.assets.get("preparation_id") in NEW_IDS | VARIANT_IDS}
    assert set(selected) == NEW_IDS | VARIANT_IDS
    builder = load_python(ROOT / "backend/scripts/build_preparation_bank.py", "batch90_material_builder")
    required = {"assumptions", "optimality", "verification", "edge_cases", "common_mistakes",
                "interview_answer", "solution_extensions", "source_ambiguities"}
    raw = {q["id"]: q for q in read(BANK / "questions.json")["questions"]}
    for ident, question in selected.items():
        original = raw[ident]
        assert original["status"] == "in_review" and original["solution_status"] == "proposed"
        assert original["ai_assisted"] and original["reviewed_by"] is None
        assert original["company_attribution_status"] == "reported_by_supplied_source_not_independently_verified"
        assert question.status == "trial" and question.reuse_status == "pending_review"
        assert not question.reviewed_by and not question.assets["assessment_ready"]
        assert question.assets["difficulty_status"] == "unrated"
        assert solution_review(question).model_dump() == {"status": "pending_review", "reviewed_on": None}
        resource = question.assets["preparation_resource"]
        assert resource["solution_status"] == "proposed" and resource["ai_assisted"]
        material = resource["learner_material"]
        expected = {key for key in builder.MATERIAL_FIELDS if original.get(key) not in (None, "", [], {})}
        assert set(material) == expected
        if ident in NEW_IDS:
            assert required <= material.keys()
            assert original["follow_up_integration_status"] == "prepared_in_archive_not_connected_to_interactive_queue"
        for field, pair in material.items():
            assert set(pair) == {"he", "en"}
            assert all(pair[lang] not in (None, "", [], {}) for lang in ("he", "en")), (ident, field)
            assert not any("\u05d0" <= char <= "\u05ea" for char in json.dumps(pair["en"], ensure_ascii=False)), (ident, field)
        for language in ("he", "en"):
            text = question.text(language)
            assert text.prompt and text.reference_solution and len(text.hints) == len(set(text.hints)) == 3
            assert not text.parity_checked
            if language == "en":
                assert not any("\u05d0" <= char <= "\u05ea" for char in text.prompt + text.reference_solution + "".join(text.hints))
            public = summary(LoadedQuestion(uuid.uuid4(), question, question.version), language)
            assert public.difficulty is None and not public.assessment_ready and not public.reviewed
            assert text.reference_solution not in public.model_dump_json()
            assert not bank._servable(question, mode="deep", language=language, allow_in_review=True, require_parity=False)


def test_new_private_assets_are_safe_hash_bound_and_localized(catalog):
    uploads = read(SEEDS / "preparation_uploads.json")["files"]
    assert_pre_batch90_assets(uploads)
    assert_pre_batch110_assets(uploads)
    assert len(BATCH110_BASELINE["asset_sha256"]) == 999
    new_paths = BATCH110_BASELINE["asset_sha256"].keys() - BASELINE["asset_sha256"].keys()
    media_by_path = {item["path"]: item for q in catalog.questions.values()
                     if q.assets.get("preparation_id") in AFFECTED_IDS for item in q.assets["bank_media"]}
    assert new_paths <= media_by_path.keys()
    assert len(new_paths) == 78
    assert sum(uploads[path]["local_path"].startswith("sources/") for path in new_paths) == 20
    assert sum(uploads[path]["local_path"].startswith("diagrams/") for path in new_paths) == 36
    assert sum(uploads[path]["local_path"].startswith("solutions/") for path in new_paths) == 22
    for path in new_paths:
        item, entry = media_by_path[path], uploads[path]
        assert question_resources.PATH.fullmatch(path)
        local = (BANK / entry["local_path"]).resolve()
        assert local.is_relative_to(BANK.resolve()) and local.is_file()
        assert item["sha256"] == entry["sha256"] == hashlib.sha256(local.read_bytes()).hexdigest()
        assert item["source_path"] == entry["local_path"]
        if item["source_path"].startswith("diagrams/"):
            assert item["caption"].strip() and item["language"] in ("he", "en")
            assert item["source_path"].endswith("-" + item["language"] + ".png")
            if item["language"] == "en":
                assert not any("\u05d0" <= char <= "\u05ea" for char in item["caption"])
    sources = [entry["local_path"] for entry in uploads.values() if entry["local_path"].startswith("sources/")]
    assert len(sources) == 311 and len(set(sources)) == 310
    names = read(ROOT / "apps/web/src/lib/source-screenshots.json")
    assert set(names) == {Path(path).name for path in sources}
    assert all(f"2026-10-30-batch90-{number:02d}.png" in names for number in range(1, 21))
    for ident in NEW_IDS:
        question = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == ident)
        for language in ("he", "en"):
            media = question_resources.learner_media(question.assets["bank_media"], language)
            assert any(item["role"] == "solution" and item.get("language") == language for item in media)
            assert all(not item["source_path"].startswith("sources/") for item in media)


def test_all_400_short_card_objects_revisions_and_2000_quiz_variants_remain_unchanged():
    content = ROOT / "apps/web/src/content"
    cards = []
    assert len(BASELINE["short_card_source_sha256"]) == 11
    for name, previous_hash in BASELINE["short_card_source_sha256"].items():
        current = read(content / name)
        assert digest(current) == previous_hash, name
        cards.extend(current)
    assert len(cards) == len({card["id"] for card in cards}) == 400
    registry = read(SEEDS / "fundamentals_catalog.json")
    assert digest(registry) == BASELINE["fundamentals_catalog_sha256"]
    assert read(content / "fundamentals-revisions.json") == registry["questions"]
    quiz = read(SEEDS / "duel_quiz.json")
    assert digest(quiz) == BASELINE["quiz_bank_sha256"]
    assert len(quiz["questions"]) == 2040
    assert sum(q["status"] == "approved" for q in quiz["questions"]) == 2000


MODEL_CASES = [
    ("hardware", "179", "prep-179-verification.json"),
    ("hardware", "180", "prep-180-verification.json"),
    ("hardware", "181", "prep-181-verification.json"),
    ("hardware", "016_lsb_priority", "prep-016-lsb-priority-batch90-verification.json"),
    ("hardware", "122_ha_fa", "prep-122-ha-fa-batch90-verification.json"),
    ("hardware", "095_six_of_seven", "prep-095-six-of-seven-batch90-verification.json"),
    ("hardware", "078_fiftieth_edge", "prep-078-fiftieth-edge-batch90-verification.json"),
    ("hardware", "076_capacity", "prep-076-capacity-batch90-verification.json"),
    *(("reasoning", str(number), f"prep-{number}-verification.json") for number in range(182, 188)),
    ("root", "178", "prep-178-verification.json"),
    ("root", "064_two_bit_batch90", "prep-064-two-bit-batch90-verification.json"),
    ("root", "072_stream_batch90", "prep-072-stream-batch90-verification.json"),
]


@pytest.mark.parametrize("domain,name,report_name", MODEL_CASES, ids=[case[1] for case in MODEL_CASES])
def test_seventeen_model_oracle_groups_reproduce_their_executed_reports(domain, name, report_name):
    checks = BANK / "checks"
    if domain == "hardware":
        module = load_python(checks / "batch90_hardware_checks.py", "batch90_hardware_test")
        result = module.CHECKS[name]()
        assert result.get("hdl_compiled") is not True
    elif domain == "reasoning":
        module = load_python(checks / "batch90_reasoning_checks.py", "batch90_reasoning_test")
        result = getattr(module, "check_" + name)()
        result.update(question_id="PREP-" + name, ai_assisted=True, professional_review="pending")
    else:
        module = load_python(checks / ("check_prep_" + name + ".py"), "batch90_root_test_" + name)
        result = module.verify()
    assert result["status"] == "passed"
    assert json.loads(json.dumps(result, ensure_ascii=False)) == read(checks / report_name)


async def test_all_19_affected_resources_preserve_ownership_and_explicit_solution_reveal(catalog, monkeypatch):
    signed = []

    async def fake_sign(media, *_):
        signed.append(media)
        return []

    monkeypatch.setattr(question_resources, "sign_media", fake_sign)
    store = InMemoryStore(catalog)
    service = PracticeService(store, catalog, scripted([]), ServiceConfig())
    owner, stranger = uuid.uuid4(), uuid.uuid4()
    questions = [q for q in catalog.questions.values() if q.assets.get("preparation_id") in AFFECTED_IDS]
    assert len(questions) == 19
    for question in questions:
        started = await service.start(owner, question_key=question.key, mode="deep", language="he")
        attempt_id = uuid.UUID(started.id)
        for language in ("he", "en"):
            hidden = await service.question_resources(owner, question.key, attempt_id=attempt_id, language=language)
            assert hidden.reference is None and hidden.technical_material is None and not hidden.solution_revealed
            assert all(item["role"] == "prompt" and item["source_path"].startswith("diagrams/") for item in signed[-1])
        with pytest.raises(ApiError) as denied:
            await service.question_resources(stranger, question.key, attempt_id=attempt_id)
        assert denied.value.code == "not_found"
        await service.reveal_reference(owner, attempt_id)
        for language in ("he", "en"):
            shown = await service.question_resources(owner, question.key, attempt_id=attempt_id, language=language)
            assert shown.solution_revealed and shown.reference == question.text(language).reference_solution
            assert shown.technical_material["id"] == question.assets["preparation_id"]
            assert shown.solution_review.status == "pending_review"
            assert signed[-1] == question_resources.learner_media(question.assets["bank_media"], language)
            assert all(not item["source_path"].startswith("sources/") for item in signed[-1])
        assert store.attempts[attempt_id]["row"]["practice_language"] == "he"
    assert not store.metrics
