"""Permanent publication/privacy contracts for the twenty-source October 24 batch.

No live credentials or database are used. Source-only records preserve the
pre-intake technical content; new material stays proposed and explicitly gated.
"""
from __future__ import annotations

import hashlib
import json
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
from tests.test_practice_hardening import scripted

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds"
NEW_IDS = {f"PREP-{number:03d}" for number in range(97, 106)}
SOURCE_MAP = {
    1: "PREP-094", 2: "PREP-097", 3: "PREP-005", 4: "PREP-072", 5: "PREP-098",
    6: "PREP-062", 7: "PREP-099", 8: "PREP-006", 9: "PREP-009", 10: "PREP-100",
    11: "PREP-067", 12: "PREP-101", 13: "PREP-029", 14: "PREP-005", 15: "PREP-102",
    16: "PREP-066", 17: "PREP-103", 18: "PREP-083", 19: "PREP-104", 20: "PREP-105",
}
# Freeze only technical version, full translations and prepared hints, allowing
# archival provenance/tags to grow. Captured before this intake's integration.
SOURCE_ONLY_TECHNICAL_SHA256 = {
    "PREP-005": "614d24202bd21cd1fa166bc51bd917321fb6f1ab08c577b2eef0fb7ce71a8b8d",
    "PREP-006": "911f4e906855fdce2422dc83add4baa0bc222448ac6d85c12357c3b336aa2a33",
    "PREP-009": "2a100a7e41cf6faea461ab15bd1fc6d947600d98273b41c9faf6e1dcb5e9d031",
    "PREP-029": "0883ee51538a4a4126890a4b02d9d3b197ae062b8500a228aba87bdabbc5f06b",
    "PREP-066": "cc7830754ac2812f0958a5c825ee9391f442316cc3978d4d4c7f2fa1adbf6012",
    "PREP-067": "8d814c1c463cf512a626d8d714751a60477263af409b5581df60bebf2d4f1475",
    "PREP-072": "d65e627e01d4e50cf66e90a88c4b29d850ea911b8a7e62b0a12b3987154dc93f",
    "PREP-083": "33d777510df846b1ecab98458efa153c5b4b4eacce6d431eccbe8aa07a81143a",
    "PREP-094": "3032a71a0cd3ca8fecdf130505bd4e2b0a0f3e4d36b8d8623fdae7e6b29a22cc",
}
# PREP-094 received an appended C variant on October 25. Reconstruct its
# original technical snapshot before hashing, preserving every prior hint and
# exact prompt/solution prefix while permitting that later version to grow.
LATER_APPEND_PREFIX_LENGTHS = {
    "PREP-094": {
        "version": 1,
        "he": {"prompt": 425, "reference_solution": 2546},
        "en": {"prompt": 513, "reference_solution": 3000},
    },
}


@pytest.fixture
def catalog():
    return load_catalog(SEEDS)


def archive():
    return json.loads((BANK / "questions.json").read_text(encoding="utf-8"))


def test_twenty_sources_have_exact_identity_mapping_and_permanent_matching_bytes():
    manifest = json.loads((BANK / "intakes/2026-10-24-batch20-sources.json").read_text(encoding="utf-8"))
    assert manifest["screenshot_count"] == len(manifest["sources"]) == 20
    assert {item["screenshot"] for item in manifest["sources"]} == set(SOURCE_MAP)
    all_questions = {item["id"]: item for item in archive()["questions"]}
    for source in manifest["sources"]:
        number = source["screenshot"]
        expected = SOURCE_MAP[number]
        assert source["question_ids"] == [expected]
        assert source["original_prompt"].strip()
        assert source["archive_paths"] == [f"sources/2026-10-24-batch20-{number:02d}.png"]
        path = source["archive_paths"][0]
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == source["sha256"]
        assert any(item.get("path") == path for item in all_questions[expected]["sources"])
    old_ids = set(SOURCE_MAP.values()) - NEW_IDS
    assert len(NEW_IDS) == 9 and len(old_ids) == 10
    assert old_ids == set(SOURCE_ONLY_TECHNICAL_SHA256) | {"PREP-062"}


def test_source_only_questions_preserve_versions_translations_and_three_hint_sets():
    questions = {item["id"]: item for item in archive()["questions"]}
    for ident, expected_hash in SOURCE_ONLY_TECHNICAL_SHA256.items():
        question = questions[ident]
        technical = json.loads(json.dumps({
            key: question.get(key) for key in ("version", "translations", "prepared_hints")
        }))
        if ident in LATER_APPEND_PREFIX_LENGTHS:
            baseline = LATER_APPEND_PREFIX_LENGTHS[ident]
            assert question["version"] >= baseline["version"] + 1, ident
            technical["version"] = baseline["version"]
            for language in ("he", "en"):
                for field, length in baseline[language].items():
                    value = technical["translations"][language][field]
                    assert len(value) > length, (ident, language, field)
                    technical["translations"][language][field] = value[:length]
        serialized = json.dumps(technical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        assert hashlib.sha256(serialized.encode()).hexdigest() == expected_hash, ident


def test_nine_new_questions_are_bilingual_pending_review_and_never_assessment_ready(catalog):
    assert len(archive()["questions"]) == 135
    assert len(catalog.questions) == 165
    additions = {q.assets.get("preparation_id"): q for q in catalog.questions.values()
                 if q.assets.get("preparation_id") in NEW_IDS}
    assert set(additions) == NEW_IDS
    required = {"assumptions", "optimality", "verification", "edge_cases", "common_mistakes",
                "interview_answer", "solution_extensions", "source_ambiguities"}
    for ident, question in additions.items():
        assert question.status == "trial" and question.reuse_status == "pending_review", ident
        assert not question.reviewed_by and not question.assets["assessment_ready"], ident
        assert question.assets["difficulty_status"] == "unrated", ident
        assert solution_review(question).model_dump() == {"status": "pending_review", "reviewed_on": None}
        resource = question.assets["preparation_resource"]
        assert resource["solution_status"] == "proposed" and resource["ai_assisted"]
        material = resource["learner_material"]
        assert required <= material.keys(), ident
        for field, pair in material.items():
            assert set(pair) == {"he", "en"}, (ident, field)
            for language in ("he", "en"):
                assert pair[language] not in (None, "", [], {}), (ident, field, language)
            assert not any("\u05d0" <= char <= "\u05ea"
                           for char in json.dumps(pair["en"], ensure_ascii=False)), (ident, field)
        for language in ("he", "en"):
            text = question.text(language)
            assert text.prompt and text.reference_solution
            assert len(text.hints) == len(set(text.hints)) == 3, (ident, language)
            assert not text.parity_checked
            if language == "en":
                assert not any("\u05d0" <= char <= "\u05ea"
                               for char in text.prompt + text.reference_solution + "".join(text.hints))
            public = summary(LoadedQuestion(uuid.uuid4(), question, question.version), language)
            assert public.preparation_id == ident
            assert public.difficulty is None and not public.assessment_ready and not public.reviewed
            assert text.reference_solution not in public.model_dump_json()
            assert not bank._servable(question, mode="deep", language=language,
                                      allow_in_review=True, require_parity=False)


def test_every_new_private_media_path_matches_the_upload_manifest_and_learner_pngs_are_localized(catalog):
    uploads = json.loads((SEEDS / "preparation_uploads.json").read_text(encoding="utf-8"))["files"]
    manifest_entries = {entry["local_path"]: entry for entry in uploads.values()}
    for question in catalog.questions.values():
        ident = question.assets.get("preparation_id")
        if ident not in NEW_IDS:
            continue
        media = question.assets["bank_media"]
        assert any(item["source_path"].startswith("sources/") for item in media)
        for item in media:
            assert item["path"].startswith(ident.lower() + "/")
            assert question_resources.PATH.fullmatch(item["path"])
            entry = manifest_entries[item["source_path"]]
            digest = hashlib.sha256((BANK / item["source_path"]).read_bytes()).hexdigest()
            assert item["sha256"] == entry["sha256"] == digest
        for language in ("he", "en"):
            learner = question_resources.learner_media(media, language)
            assert learner
            assert all(not item["source_path"].startswith("sources/") for item in learner)
            diagrams = [item for item in learner if item["filename"].endswith(".png")]
            assert diagrams and any(item["role"] == "solution" for item in diagrams)
            assert all(item["source_path"].startswith("diagrams/") and item.get("language") == language
                       for item in diagrams)


async def test_new_resources_require_owned_reveal_and_never_sign_archived_sources(catalog, monkeypatch):
    signed = []

    async def fake_sign(media, *_):
        signed.append(media)
        return []

    monkeypatch.setattr(question_resources, "sign_media", fake_sign)
    store = InMemoryStore(catalog)
    service = PracticeService(store, catalog, scripted([]), ServiceConfig())
    user, stranger = uuid.uuid4(), uuid.uuid4()
    questions = [q for q in catalog.questions.values() if q.assets.get("preparation_id") in NEW_IDS]
    assert len(questions) == 9
    for question in questions:
        ident = question.assets["preparation_id"]
        started = await service.start(user, question_key=question.key, mode="deep", language="he")
        attempt_id = uuid.UUID(started.id)
        for language in ("he", "en"):
            hidden = await service.question_resources(user, question.key, attempt_id=attempt_id, language=language)
            assert hidden.reference is None and hidden.technical_material is None and not hidden.solution_revealed
            assert all(item["role"] == "prompt" and item["source_path"].startswith("diagrams/")
                       and item.get("language") == language for item in signed[-1])
            if ident == "PREP-104":
                assert [item["filename"] for item in signed[-1]] == [f"prep-104-prompt-pipeline-{language}.png"]
        with pytest.raises(ApiError) as denied:
            await service.question_resources(stranger, question.key, attempt_id=attempt_id)
        assert denied.value.code == "not_found"
        await service.reveal_reference(user, attempt_id)
        for language in ("he", "en"):
            revealed = await service.question_resources(user, question.key, attempt_id=attempt_id, language=language)
            assert revealed.solution_revealed and revealed.reference == question.text(language).reference_solution
            assert revealed.technical_material["id"] == ident
            assert revealed.solution_review.status == "pending_review"
            assert signed[-1] == question_resources.learner_media(question.assets["bank_media"], language)
            assert any(item["role"] == "solution" for item in signed[-1])
            assert all(not item["source_path"].startswith("sources/") for item in signed[-1])
        assert store.attempts[attempt_id]["row"]["practice_language"] == "he"
    assert not store.metrics
