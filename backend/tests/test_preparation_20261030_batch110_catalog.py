"""Permanent contracts for twenty supplied sources and eleven new study questions.

All service checks are in-memory. The fifteen model checks are finite exact
software/numerical oracles; no live learner writes or C/C++/HDL compilation occur.
The destructor illustration has a separate static contract, without an execution claim.
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
    BATCH21_BASELINE,
    BATCH110_BASELINE,
    assert_pre_batch21_assets,
    assert_pre_batch110_archive,
    assert_pre_batch110_assets,
    digest,
)
from tests.test_practice_hardening import scripted

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds"
NEW_IDS = {f"PREP-{number}" for number in range(188, 199)}
VARIANT_IDS = {"PREP-022", "PREP-039", "PREP-073", "PREP-125", "PREP-149"}
SOURCE_ONLY_IDS = {"PREP-018", "PREP-031", "PREP-044", "PREP-047"}
AFFECTED_IDS = NEW_IDS | VARIANT_IDS | SOURCE_ONLY_IDS
# Final content-addressed additions; all 999 pre-intake assets stay frozen.
NEW_ASSET_COUNT = 71
NEW_DIAGRAM_COUNT = 32
NEW_CODE_COUNT = 19
SOURCE_MAP = dict(enumerate((188, 22, 47, 125, 149, 189, 190, 191, 31, 192,
                             193, 18, 194, 39, 195, 196, 197, 198, 44, 73), 1))


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
    intake = read(BANK / "intakes/2026-10-30-batch110-sources.json")
    archive = {question["id"]: question for question in read(BANK / "questions.json")["questions"]}
    assert intake["screenshot_count"] == intake["question_source_count"] == len(intake["sources"]) == 20
    assert {source["screenshot"] for source in intake["sources"]} == set(SOURCE_MAP)
    for source in intake["sources"]:
        number = source["screenshot"]
        ident = f"PREP-{SOURCE_MAP[number]:03d}"
        path = f"sources/2026-10-30-batch110-{number:02d}.png"
        assert source["archive_paths"] == [path] and source["question_ids"] == [ident]
        assert source["original_prompt"].strip()
        assert source["sha256"] == BATCH110_BASELINE["batch110_source_sha256"][str(number)]
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == source["sha256"]
        question = archive[ident]
        assert any(item.get("path") == path for item in question["sources"])
        assert set(source["source_tags"]) <= set(question["source_tags"])
        assert set(source["reported_companies"]) <= set(question["reported_companies"])
        expected = ("new_manual_question" if ident in NEW_IDS else "existing_question_source_and_variant"
                    if ident in VARIANT_IDS else "additional_source_existing_question")
        assert source["decision"] == expected
    assert len(AFFECTED_IDS) == 20
    assert sum(f"PREP-{number:03d}" in VARIANT_IDS for number in SOURCE_MAP.values()) == 5


def test_authorized_extensions_preserve_all_186_original_records_and_999_assets(catalog):
    archive = read(BANK / "questions.json")
    assert len(archive["questions"]) == 219 and len(catalog.questions) == 249
    previous_ids = {question["id"] for question in archive["questions"] if int(question["id"].split("-")[1]) <= 198}
    assert previous_ids - set(BATCH110_BASELINE["records"]) == NEW_IDS
    assert_pre_batch110_archive(archive)
    assert_pre_batch110_assets(read(SEEDS / "preparation_uploads.json")["files"])
    # These three explicit existing aliases remain the only collapsed families.
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
    builder = load_python(ROOT / "backend/scripts/build_preparation_bank.py", "batch110_material_builder")
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
                previous = BATCH110_BASELINE["records"][ident]["projection"]["append_shapes"]["translations"]["items"][language]["items"]
                for field in ("prompt", "reference_solution"):
                    addition = original["translations"][language][field][previous[field]["length"]:]
                    assert addition.strip() and addition.strip() in getattr(text, field), (ident, language, field)
                    compiled_prefix = BATCH110_BASELINE["compiled_variant_prefixes"][ident][language][field]
                    assert digest(getattr(text, field)[:compiled_prefix["length"]]) == compiled_prefix["sha256"], (ident, language, field)
            if language == "en":
                assert not any("\u05d0" <= char <= "\u05ea" for char in text.prompt + text.reference_solution + "".join(text.hints))
            public = summary(LoadedQuestion(uuid.uuid4(), question, question.version), language)
            assert public.difficulty is None and not public.assessment_ready and not public.reviewed
            assert text.reference_solution not in public.model_dump_json()
            assert not bank._servable(question, mode="deep", language=language, allow_in_review=True, require_parity=False)


def test_new_private_assets_are_safe_hash_bound_and_localized(catalog):
    uploads = read(SEEDS / "preparation_uploads.json")["files"]
    assert_pre_batch110_assets(uploads)
    assert_pre_batch21_assets(uploads)
    assert len(BATCH110_BASELINE["asset_sha256"]) == 999
    new_paths = BATCH21_BASELINE["asset_sha256"].keys() - BATCH110_BASELINE["asset_sha256"].keys()
    media_by_path = {item["path"]: item for q in catalog.questions.values()
                     if q.assets.get("preparation_id") in AFFECTED_IDS for item in q.assets["bank_media"]}
    assert new_paths <= media_by_path.keys()
    assert len(BATCH21_BASELINE["asset_sha256"]) == 1070 and len(new_paths) == NEW_ASSET_COUNT
    assert sum(uploads[path]["local_path"].startswith("sources/") for path in new_paths) == 20
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
    assert all(f"2026-10-30-batch110-{number:02d}.png" in names for number in range(1, 21))
    for ident in NEW_IDS:
        question = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == ident)
        for language in ("he", "en"):
            media = question_resources.learner_media(question.assets["bank_media"], language)
            assert any(item["role"] == "solution" and item.get("language") == language for item in media)
            assert all(not item["source_path"].startswith("sources/") for item in media)


def test_all_400_short_card_objects_revisions_and_2000_quiz_variants_remain_unchanged():
    content = ROOT / "apps/web/src/content"
    cards = []
    assert len(BATCH110_BASELINE["short_card_source_sha256"]) == 11
    for name, previous_hash in BATCH110_BASELINE["short_card_source_sha256"].items():
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
    assert digest(historical_registry) == BATCH110_BASELINE["fundamentals_catalog_sha256"]
    assert read(content / "fundamentals-revisions.json") == registry["questions"]
    quiz = read(SEEDS / "duel_quiz.json")["questions"]
    historical_quiz = [q for q in quiz if not q.get("source_key")
                       or int(q["source_key"].rsplit("-", 1)[1]) <= 200]
    assert digest(sorted(historical_quiz, key=lambda q: q["key"])) == (
        "d5658c38b6abbad3a0354993738e751e5a376a1a8cbbbf15efabf38a4e4067af"
    )
    assert len(historical_quiz) == 2040
    assert sum(q["status"] == "approved" for q in historical_quiz) == 2000


MODEL_CASES = [
    *(("root", str(n), f"prep-{n}-verification.json") for n in (188, 194, 196)),
    *(("root", f"{n:03d}", f"prep-{n:03d}-batch110-verification.json") for n in (22, 125, 149)),
    *(("hardware", str(n), f"prep-{n}-verification.json") for n in (191, 193, 197)),
    ("hardware", "73", "prep-073-ninety-minutes-batch110-verification.json"),
    *(("reasoning", str(n), f"prep-{n}-verification.json") for n in (190, 192, 195, 198)),
    ("reasoning", "039-canoe-batch110", "prep-039-canoe-batch110-verification.json"),
]


@pytest.mark.parametrize("domain,name,report_name", MODEL_CASES, ids=[case[1] for case in MODEL_CASES])
def test_fifteen_finite_oracle_groups_reproduce_their_executed_reports(domain, name, report_name):
    checks = BANK / "checks"
    if domain == "hardware":
        module = load_python(checks / "batch110_hardware_checks.py", "batch110_hardware_test")
        result = module.CHECKS[int(name)]()
        assert result["status"] == "pass"
    elif domain == "reasoning":
        module = load_python(checks / "batch110_reasoning_checks.py", "batch110_reasoning_test")
        result = module.CHECKS[name]()
        assert result["status"] == "passed"
    else:
        module = load_python(checks / "check_batch110_root.py", "batch110_root_test")
        result = module.run_group("PREP-" + name)
        assert result["passed"] is True and result["professional_review"] == "pending"
    assert json.loads(json.dumps(result, ensure_ascii=False)) == read(checks / report_name)


def test_destructor_illustration_owns_resources_and_supports_its_polymorphic_delete(catalog):
    """Inspect declaration relationships, without pretending regex is a compiler."""
    path = BANK / "solutions/prep_189_destructor_raii.cpp"
    source = path.read_text("utf-8")
    code = re.sub(r"//[^\n]*|/\*.*?\*/", "", source, flags=re.DOTALL)
    # Extract the declared owning base and dynamic derived type from main, then
    # check the destructibility obligation created by that actual relationship.
    base, derived = re.search(
        r"std::unique_ptr<(\w+)>\s+\w+\s*=\s*std::make_unique<(\w+)>\(\)", code
    ).groups()
    classes = {name: (parents, body) for name, parents, body in re.findall(
        r"struct\s+(\w+)\s*([^\{]*)\{(.*?)\n\};", code, re.DOTALL
    )}
    assert re.search(rf":\s*(?:public\s+)?{base}\b", classes[derived][0])
    assert re.search(rf"virtual\s+~{base}\s*\(\)\s*=\s*default\s*;", classes[base][1])
    assert re.search(r"std::unique_ptr<int\[\]>\s+\w+\s*=\s*std::make_unique<int\[\]>\(16\)", classes[derived][1])
    assert not re.search(r"\bdelete\b|\bnew\b", code)
    value_classes = [body for name, (_, body) in classes.items() if name not in (base, derived)]
    assert len(value_classes) == 1
    assert "std::string" in value_classes[0] and "std::vector<int>" in value_classes[0]
    assert not any("~" in body for body in value_classes)
    assert not re.search(rf"~{derived}\s*\(", classes[derived][1])

    report = read(BANK / "checks/prep-189-verification.json")
    assert report == {
        "question_id": "PREP-189", "status": "primary_reference_and_source_review_only",
        "compiled": False, "executed_cpp": False, "professional_review": "pending",
        "reference": "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines",
    }
    question = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == "PREP-189")
    for language in ("he", "en"):
        assert source.strip() in question.text(language).reference_solution
    material = question.assets["preparation_resource"]["learner_material"]
    assert "No C++ compilation" in material["verification"]["en"]
    assert "undefined" in question.text("en").reference_solution
    assert any("#c35-" in item["url"] for item in material["technical_references"]["en"])


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
