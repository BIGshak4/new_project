"""Permanent contracts for twenty-one supplied sources and eleven new study questions.

All service checks are in-memory. The sixteen model checks are finite exact
software/numerical oracles; no live learner writes or C/C++/HDL compilation occur.
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
    BATCH20_BASELINE,
    BATCH21_BASELINE,
    assert_pre_batch20_assets,
    assert_pre_batch21_archive,
    assert_pre_batch21_assets,
    assert_pre_batch21_localization,
    digest,
)
from tests.test_practice_hardening import scripted

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds"
NEW_IDS = {f"PREP-{number}" for number in range(199, 210)}
VARIANT_IDS = {"PREP-011", "PREP-081", "PREP-094", "PREP-102", "PREP-162"}
SOURCE_ONLY_IDS = {"PREP-057", "PREP-083", "PREP-141", "PREP-166"}
AFFECTED_IDS = NEW_IDS | VARIANT_IDS | SOURCE_ONLY_IDS
# Final content-addressed additions; all 1070 pre-intake assets stay frozen.
NEW_ASSET_COUNT = 71
NEW_DIAGRAM_COUNT = 32
NEW_CODE_COUNT = 18
SOURCE_MAP = dict(enumerate((199, 200, 201, 166, 202, 102, 162, 83, 203, 57,
                             11, 81, 204, 205, 206, 207, 141, 208, 94, 81, 209), 1))


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


def test_twenty_one_sources_keep_the_exact_original_bytes_and_identity_mapping():
    intake = read(BANK / "intakes/2026-10-31-batch21-sources.json")
    archive = {question["id"]: question for question in read(BANK / "questions.json")["questions"]}
    assert intake["screenshot_count"] == intake["question_source_count"] == len(intake["sources"]) == 21
    assert {source["screenshot"] for source in intake["sources"]} == set(SOURCE_MAP)
    for source in intake["sources"]:
        number = source["screenshot"]
        ident = f"PREP-{SOURCE_MAP[number]:03d}"
        path = f"sources/2026-10-31-batch21-{number:02d}.png"
        assert source["archive_paths"] == [path] and source["question_ids"] == [ident]
        assert source["original_prompt"].strip()
        assert source["sha256"] == BATCH21_BASELINE["batch21_source_sha256"][str(number)]
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == source["sha256"]
        question = archive[ident]
        assert any(item.get("path") == path for item in question["sources"])
        assert set(source["source_tags"]) <= set(question["source_tags"])
        assert set(source["reported_companies"]) <= set(question["reported_companies"])
        expected = ("new_manual_question" if ident in NEW_IDS else "existing_question_source_and_variant"
                    if ident in VARIANT_IDS else "additional_source_existing_question")
        assert source["decision"] == expected
    assert len(AFFECTED_IDS) == 20
    assert sum(f"PREP-{number:03d}" in VARIANT_IDS for number in SOURCE_MAP.values()) == 6


def test_authorized_extensions_preserve_all_197_original_records_and_1070_assets(catalog):
    archive = read(BANK / "questions.json")
    assert len(archive["questions"]) == 219 and len(catalog.questions) == 249
    # Freeze this intake's 208-record endpoint before projecting its 197-record
    # predecessor. The later eleven additions have their own batch20 tests.
    previous_ids = {question["id"] for question in archive["questions"]
                    if question["id"] in BATCH20_BASELINE["records"]}
    assert len(previous_ids) == 208
    assert previous_ids - set(BATCH21_BASELINE["records"]) == NEW_IDS
    assert_pre_batch21_archive(archive)
    assert_pre_batch21_assets(read(SEEDS / "preparation_uploads.json")["files"])
    localization = {}
    for path in sorted((SEEDS / "preparation_localization").glob("*.json")):
        entries = read(path)
        assert not localization.keys() & entries.keys(), path
        localization.update(entries)
    historical_ids = localization.keys() & BATCH20_BASELINE["localized_material"].keys()
    assert historical_ids - BATCH21_BASELINE["localized_material"].keys() == NEW_IDS
    assert_pre_batch21_localization(localization)
    # The three old aliases stay intact, plus the explicitly audited modulo-six example.
    module = (ROOT / "apps/web/src/lib/question-families.ts").read_text("utf-8")
    pairs = re.findall(r'^\s*"([^"]+)":\s*"([^"]+)",', module, re.MULTILINE)
    aliases = dict(pairs)
    assert aliases == {
        "example-power-of-two-check": "prep-power-of-two-check",
        "example-merge-measurement-streams": "prep-merge-two-sorted-arrays",
        "example-overlapping-sequence-1011": "prep-detect-overlapping-1011-stream",
        "example-mod-six-counter": "prep-enabled-mod-six-counter",
    }
    assert set(aliases) | set(aliases.values()) <= catalog.questions.keys()
    assert len({aliases.get(key, key) for key in catalog.questions}) == 245


def test_all_new_questions_and_extensions_remain_bilingual_proposed_unrated_and_gated(catalog):
    selected = {q.assets.get("preparation_id"): q for q in catalog.questions.values()
                if q.assets.get("preparation_id") in NEW_IDS | VARIANT_IDS}
    assert set(selected) == NEW_IDS | VARIANT_IDS
    builder = load_python(ROOT / "backend/scripts/build_preparation_bank.py", "batch21_material_builder")
    required = {"assumptions", "optimality", "verification", "edge_cases", "common_mistakes",
                "interview_answer", "solution_extensions", "source_ambiguities"}
    raw = {q["id"]: q for q in read(BANK / "questions.json")["questions"]}
    for ident, question in selected.items():
        original = raw[ident]
        assert original["status"] == "in_review" and original["solution_status"] == "proposed"
        assert original["ai_assisted"] and original["reviewed_by"] is None
        attribution = ("reported_by_supplied_source_not_independently_verified" if original["reported_companies"]
                       else "no_company_attribution_in_supplied_source")
        assert original["company_attribution_status"] == attribution
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
            if ident in VARIANT_IDS:
                previous = BATCH21_BASELINE["records"][ident]["projection"]["append_shapes"]["translations"]["items"][language]["items"]
                for field in ("prompt", "reference_solution"):
                    addition = original["translations"][language][field][previous[field]["length"]:]
                    assert addition.strip() and addition.strip() in getattr(text, field), (ident, language, field)
                    compiled_prefix = BATCH21_BASELINE["compiled_variant_prefixes"][ident][language][field]
                    assert digest(getattr(text, field)[:compiled_prefix["length"]]) == compiled_prefix["sha256"], (ident, language, field)
            if language == "en":
                assert not any("\u05d0" <= char <= "\u05ea" for char in text.prompt + text.reference_solution + "".join(text.hints))
            public = summary(LoadedQuestion(uuid.uuid4(), question, question.version), language)
            assert public.difficulty is None and not public.assessment_ready and not public.reviewed
            assert text.reference_solution not in public.model_dump_json()
            assert not bank._servable(question, mode="deep", language=language, allow_in_review=True, require_parity=False)


def test_new_private_assets_are_safe_hash_bound_and_localized(catalog):
    uploads = read(SEEDS / "preparation_uploads.json")["files"]
    assert_pre_batch21_assets(uploads)
    assert_pre_batch20_assets(uploads)
    assert len(BATCH21_BASELINE["asset_sha256"]) == 1070
    new_paths = BATCH20_BASELINE["asset_sha256"].keys() - BATCH21_BASELINE["asset_sha256"].keys()
    media_by_path = {item["path"]: item for q in catalog.questions.values()
                     if q.assets.get("preparation_id") in AFFECTED_IDS for item in q.assets["bank_media"]}
    assert new_paths <= media_by_path.keys()
    assert len(BATCH20_BASELINE["asset_sha256"]) == 1070 + NEW_ASSET_COUNT
    assert len(new_paths) == NEW_ASSET_COUNT
    assert sum(uploads[path]["local_path"].startswith("sources/") for path in new_paths) == 21
    assert sum(uploads[path]["local_path"].startswith("diagrams/") for path in new_paths) == NEW_DIAGRAM_COUNT
    assert sum(uploads[path]["local_path"].startswith("solutions/") for path in new_paths) == NEW_CODE_COUNT
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
    assert len(sources) == 352 and len(set(sources)) == 351
    names = read(ROOT / "apps/web/src/lib/source-screenshots.json")
    assert set(names) == {Path(path).name for path in sources}
    assert all(f"2026-10-31-batch21-{number:02d}.png" in names for number in range(1, 22))
    for ident in NEW_IDS:
        question = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == ident)
        for language in ("he", "en"):
            media = question_resources.learner_media(question.assets["bank_media"], language)
            assert any(item["role"] == "solution" and item.get("language") == language for item in media)
            assert all(not item["source_path"].startswith("sources/") for item in media)


def test_all_400_short_card_objects_revisions_and_2000_quiz_variants_remain_unchanged():
    content = ROOT / "apps/web/src/content"
    cards = []
    assert len(BATCH21_BASELINE["short_card_source_sha256"]) == 11
    for name, previous_hash in BATCH21_BASELINE["short_card_source_sha256"].items():
        current = read(content / name)
        assert digest(current) == previous_hash, name
        cards.extend(current)
    assert len(cards) == len({card["id"] for card in cards}) == 400
    registry = read(SEEDS / "fundamentals_catalog.json")
    # Later authorized expansions add keys, while this intake's content stays frozen.
    historical_registry = {**registry, "questions": {
        key: revision for key, revision in registry["questions"].items()
        if int(key.rsplit("-", 1)[1]) <= 200
    }}
    assert len(historical_registry["questions"]) == 400
    assert digest(historical_registry) == BATCH21_BASELINE["fundamentals_catalog_sha256"]
    assert read(content / "fundamentals-revisions.json") == registry["questions"]
    quiz = read(SEEDS / "duel_quiz.json")["questions"]
    historical_quiz = [q for q in quiz if not q.get("source_key")
                       or int(q["source_key"].rsplit("-", 1)[1]) <= 200]
    assert digest(sorted(historical_quiz, key=lambda q: q["key"])) == (
        "d5658c38b6abbad3a0354993738e751e5a376a1a8cbbbf15efabf38a4e4067af"
    )
    assert len(historical_quiz) == 2040
    assert sum(q["status"] == "approved" for q in historical_quiz) == 2000
    reviews = read(SEEDS / "solution_review_attestations.json")
    assert digest(reviews) == BATCH21_BASELINE["review_registry_canonical_sha256"]
    assert len(reviews["questions"]) == 93


MODEL_CASES = [
    *(("hardware", str(n), f"prep-{n}-verification.json") for n in (199, 200, 202, 204, 205, 207)),
    *(("hardware", f"{n:03d}", f"prep-{n:03d}-batch21-verification.json") for n in (11, 94, 102)),
    *(("reasoning", str(n), f"prep-{n}-verification.json") for n in (203, 206)),
    ("reasoning", "162-array-batch21", "prep-162-array-batch21-verification.json"),
    ("reasoning", "081-time-batch21", "prep-081-time-batch21-verification.json"),
    *(("root", str(n), f"prep-{n}-verification.json") for n in (201, 208, 209)),
]


@pytest.mark.parametrize("domain,name,report_name", MODEL_CASES, ids=[case[1] for case in MODEL_CASES])
def test_sixteen_finite_oracle_groups_reproduce_their_executed_reports(domain, name, report_name):
    checks = BANK / "checks"
    if domain == "hardware":
        module = load_python(checks / "batch21_hardware_checks.py", "batch21_hardware_test")
        result = module.CHECKS[int(name)]()
        assert result["status"] == "pass"
    elif domain == "reasoning":
        module = load_python(checks / "batch21_reasoning_checks.py", "batch21_reasoning_test")
        result = module.CHECKS[name]()
        assert result["status"] == "passed"
    else:
        module = load_python(checks / "check_batch21_root_20261031.py", "batch21_root_test")
        result = module.run_group("PREP-" + name)
        assert result["passed"] is True and result["professional_review"] == "pending"
    assert json.loads(json.dumps(result, ensure_ascii=False)) == read(checks / report_name)


async def test_all_20_affected_resources_preserve_ownership_and_explicit_solution_reveal(catalog, monkeypatch):
    signed = []

    async def fake_sign(media, *_):
        signed.append(media)
        return []

    monkeypatch.setattr(question_resources, "sign_media", fake_sign)
    store = InMemoryStore(catalog)
    service = PracticeService(store, catalog, scripted([]), ServiceConfig())
    owner, stranger = uuid.uuid4(), uuid.uuid4()
    questions = [q for q in catalog.questions.values() if q.assets.get("preparation_id") in AFFECTED_IDS]
    assert len(questions) == 20
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
            assert shown.solution_review.status == solution_review(question).status
            assert signed[-1] == question_resources.learner_media(question.assets["bank_media"], language)
            assert all(not item["source_path"].startswith("sources/") for item in signed[-1])
        assert store.attempts[attempt_id]["row"]["practice_language"] == "he"
    assert not store.metrics
