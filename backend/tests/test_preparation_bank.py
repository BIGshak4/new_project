"""Archive fidelity, hidden solutions, study-only evidence and source-image grading boundaries."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import uuid
from pathlib import Path

import pytest

from app.api.errors import ApiError
from app.engine import bank, evaluator
from app.engine.catalog import load_catalog
from app.engine.solution_review import solution_review
from app.repo.questions import LoadedQuestion, summary
from app.services import question_resources
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_practice_hardening import GOOD, SEEDS, scripted

ROOT = Path(__file__).resolve().parents[2]
THIRD_INTAKE_IDS = {f"PREP-{number:03d}" for number in range(74, 83)}
FOURTH_INTAKE_IDS = {f"PREP-{number:03d}" for number in range(83, 89)}
FIFTH_INTAKE_IDS = {f"PREP-{number:03d}" for number in range(89, 97)}


@pytest.fixture
def catalog():
    return load_catalog(SEEDS)


def test_compilation_preserves_every_question_and_all_original_images(catalog):
    source = json.loads((ROOT / "interview_preparation/questions.json").read_text(encoding="utf-8-sig"))
    editorial = json.loads((SEEDS / "preparation_editorial.json").read_text(encoding="utf-8"))
    manifest = json.loads((SEEDS / "preparation_uploads.json").read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("prep_builder", ROOT / "backend/scripts/build_preparation_bank.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    built, uploads = builder.load()
    assert built == json.loads((SEEDS / "questions/preparation_bank.json").read_text(encoding="utf-8"))
    assert uploads == manifest["files"]
    assert len(source["questions"]) == len(built) == 197
    for q in built:
        for media in q["assets"]["bank_media"]:
            if any(word in media["filename"] for word in ("external-answer", "clarification", "style-reference", "course-adder-summary")):
                assert media["role"] == "solution", "An explanation screenshot must never leak before reference reveal"
    assert len(catalog.questions) == 227
    archived_images = {p.relative_to(ROOT / "interview_preparation").as_posix()
                       for folder in ("sources", "diagrams")
                       for p in (ROOT / "interview_preparation" / folder).glob("*.png")}
    assert archived_images <= {m["local_path"] for m in uploads.values()}
    for m in uploads.values():
        assert hashlib.sha256((ROOT / "interview_preparation" / m["local_path"]).read_bytes()).hexdigest() == m["sha256"]
    for original in source["questions"]:
        q = catalog.questions["prep-" + original["key"]]
        assert q.assets["source_sha256"] == hashlib.sha256(json.dumps(original, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        assert q.assets["topics"] == original["topics"]
        assert q.assets["reported_companies"] == original["reported_companies"]
        resource = q.assets["preparation_resource"]
        assert not ({"hint_history", "discussion_summary", "solution_disclosure"} & resource.keys())
        for lang in ("en", "he"):
            overrides = editorial[original["id"]].get("learner_text", {}).get(lang, {})
            assert q.text(lang).prompt == overrides.get("prompt", original["translations"][lang]["prompt"])
            if "reference_solution" in overrides:
                assert q.text(lang).reference_solution == overrides["reference_solution"]
            assert q.text(lang).reference_solution
            assert len(q.text(lang).hints) == 3
        s = summary(LoadedQuestion(uuid.uuid4(), q, q.version), "he")
        assert s.difficulty is None and not s.assessment_ready and not s.reviewed
        assert s.companies == []
        assert not ({"reference_solution", "preparation_resource", "bank_media"} & s.model_dump().keys())
        assert not bank._servable(q, mode="deep", language="he", allow_in_review=True, require_parity=False)


async def test_resource_exposure_requires_own_matching_revealed_attempt(catalog, monkeypatch):
    signed = []
    async def fake_sign(media, *_):
        signed.append(media)
        return []
    monkeypatch.setattr(question_resources, "sign_media", fake_sign)
    q = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == "PREP-001")
    user, stranger = uuid.uuid4(), uuid.uuid4()
    svc = PracticeService(InMemoryStore(catalog), catalog, scripted([GOOD]), ServiceConfig())
    public = await svc.question_resources(user, q.key)
    assert public.technical_material is None and not public.solution_revealed
    assert all(m["role"] == "prompt" for m in signed[-1])
    a = await svc.start(user, question_key=q.key, mode="deep", language="he")
    aid = uuid.UUID(a.id)
    with pytest.raises(ApiError) as denied:
        await svc.question_resources(stranger, q.key, attempt_id=aid)
    assert denied.value.code == "not_found"
    with pytest.raises(ApiError):
        await svc.question_resources(user, "example-sensor-majority", attempt_id=aid)
    hidden = await svc.question_resources(user, q.key, attempt_id=aid)
    assert hidden.technical_material is None
    await svc.reveal_reference(user, aid)
    shown = await svc.question_resources(user, q.key, attempt_id=aid)
    assert shown.solution_revealed and shown.technical_material["id"] == "PREP-001"
    assert signed[-1] == question_resources.learner_media(q.assets["bank_media"], language="he")
    assert all(not m.get("source_path", "").startswith("sources/") for m in signed[-1])


async def test_unrated_feedback_keeps_profile_metrics_and_xp_unchanged(catalog):
    q = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == "PREP-001")
    user = uuid.uuid4()
    store = InMemoryStore(catalog)
    provider = scripted([GOOD])
    async def images(_):
        return [("image/png", b"source diagram")]
    svc = PracticeService(store, catalog, provider, ServiceConfig(), question_image_fetcher=images)
    before = copy.deepcopy(store.profiles)
    a = await svc.start(user, question_key=q.key, mode="deep", language="he")
    aid = uuid.UUID(a.id)
    await svc.next_hint(user, aid)
    sub, view = await svc.submit(user, aid, "I count every input bit with a balanced adder tree.", idempotency_key="prepared")
    assert sub.status == "done" and "content_review_pending" in sub.flags
    assert store.profiles == before and not store.metrics
    assert sub.xp_earned == 0 and sub.next_question is None and view.pending_follow_up is None
    assert not await store_score_rows(store, user)


async def store_score_rows(store, user):
    async with store.transaction() as tx:
        return await tx.scored_submissions(user)


async def test_missing_source_diagram_saves_answer_without_guessing(catalog):
    q = next(q for q in catalog.questions.values()
             if any(m["role"] == "prompt" for m in q.assets.get("bank_media", [])))
    user = uuid.uuid4()
    provider = scripted([GOOD])
    svc = PracticeService(InMemoryStore(catalog), catalog, provider, ServiceConfig())
    a = await svc.start(user, question_key=q.key, mode="deep", language="en")
    sub, _ = await svc.submit(user, uuid.UUID(a.id), "My answer remains saved.", idempotency_key="missing")
    assert sub.status == "failed" and "question_images_unavailable" in sub.flags
    assert sub.answer == "My answer remains saved." and sub.band is None and not provider.requests


async def test_question_images_are_separated_from_candidate_work():
    provider = scripted([GOOD])
    source, answer = ("image/png", b"question"), ("image/png", b"answer")
    await evaluator.evaluate(provider, question_context="source", known_error_keys=set(), language="he", difficulty=5,
                             answer="explanation", question_images=[source], images=[answer])
    request = provider.requests[0]
    assert request.images == [source, answer]
    assert "FIRST 1" in request.user and "NOT the candidate's answer" in request.user


async def test_unsafe_storage_path_is_rejected_before_network():
    with pytest.raises(ApiError):
        await question_resources.sign_media([{"path": "../../other-bucket/file"}], "https://example.test", "key")


async def test_archive_screenshots_never_receive_learner_links(catalog):
    archive = [m for q in catalog.questions.values() for m in q.assets.get("bank_media", [])
               if m.get("source_path", "").startswith("sources/")]
    assert len(archive) == 311
    # No credentials or network needed: the boundary applies before signing.
    assert await question_resources.sign_media(archive, "", "") == []
    all_media = [m for q in catalog.questions.values() for m in q.assets.get("bank_media", [])]
    retained = question_resources.learner_media(all_media)
    assert retained and len(retained) + len(archive) == len(all_media)
    assert all(m["source_path"].startswith(("diagrams/", "solutions/")) for m in retained)


def test_additional_linked_list_source_keeps_the_edited_identity_contract(catalog):
    question = catalog.questions["prep-linked-lists-first-shared-node"]
    english = question.text("en").prompt
    hebrew = question.text("he").prompt
    assert "finite, acyclic" in english and "identical node in memory" in english
    assert "Do not modify either list" in english and "report no intersection" in english
    assert "ללא מעגלים" in hebrew and "אין לשנות את הרשימות" in hebrew
    assert "switch heads" in question.text("en").reference_solution


def test_third_intake_is_bilingual_study_only_and_preserves_frozen_solution_reviews(catalog):
    additions = {q.assets.get("preparation_id"): q for q in catalog.questions.values()
                 if q.assets.get("preparation_id") in THIRD_INTAKE_IDS}
    assert set(additions) == THIRD_INTAKE_IDS
    mandatory_material = {"assumptions", "verification", "edge_cases", "common_mistakes",
                          "interview_answer", "solution_extensions"}
    for ident, question in additions.items():
        assert question.status == "trial" and question.reuse_status == "pending_review", ident
        assert not question.reviewed_by and not question.assets["assessment_ready"], ident
        assert question.assets["difficulty_status"] == "unrated", ident
        assert solution_review(question).model_dump() == {"status": "pending_review", "reviewed_on": None}
        resource = question.assets["preparation_resource"]
        assert resource["solution_status"] == "proposed" and resource["ai_assisted"], ident
        material = resource["learner_material"]
        assert mandatory_material <= material.keys(), ident
        for field, values in material.items():
            assert set(values) == {"he", "en"}, (ident, field)
            for language in ("he", "en"):
                assert values[language] not in (None, "", [], {}), (ident, field, language)
        for field in mandatory_material:
            he = json.dumps(material[field]["he"], ensure_ascii=False)
            en = json.dumps(material[field]["en"], ensure_ascii=False)
            assert any("\u05d0" <= char <= "\u05ea" for char in he), (ident, field)
            assert not any("\u05d0" <= char <= "\u05ea" for char in en), (ident, field)
        for language in ("he", "en"):
            text = question.text(language)
            assert text.prompt and text.reference_solution and len(text.hints) == 3, (ident, language)
            assert len(set(text.hints)) == 3, (ident, language)
            assert not text.parity_checked, "Bilingual preparation does not grant human parity approval"
            safe = summary(LoadedQuestion(uuid.uuid4(), question, question.version), language)
            assert safe.preparation_id == ident and not safe.assessment_ready
            assert not safe.reviewed and safe.difficulty is None
            assert text.reference_solution not in safe.model_dump_json(), ident

    # The new batch cannot inherit an attestation. The separately rewritten
    # Rewritten/expanded PREP records no longer match their frozen attestations.
    registry = json.loads((SEEDS / "solution_review_attestations.json").read_text(encoding="utf-8"))
    reviewed = {q.key for q in catalog.questions.values() if solution_review(q).status == "human_reviewed"}
    assert len(registry["questions"]) == 93
    assert reviewed == set(registry["questions"]) - {
        "prep-seventeen-prisoners-two-mandatory-switches",
        "prep-identical-robots-trains-static-marker-rendezvous",
        "prep-xor-mux-zero-only",
        "prep-one-two-missing-values",
        "prep-three-bit-up-down-counter-gates",
        "prep-eight-bit-popcount-adders",
        "prep-three-color-in-place-partition",
        "prep-twenty-one-prisoners-one-light",
        "prep-circuit-from-clock-input-output-waveforms",
        "prep-serial-safe-abcd-sequence-detector",
        "prep-twenty-five-horses",
        "prep-dark-room-ten-tails-equal-groups",
        "prep-balanced-brackets-mixed-text",
        "prep-doorway-occupancy-two-sensors",
        "prep-sixteen-input-interrupt-controller",
        "prep-random-permutation-fisher-yates",
        "prep-bridge-torch-twelve-hours",
    }
    assert not (set(q.key for q in additions.values()) & reviewed)


async def test_third_intake_resource_reveal_keeps_sources_private_and_prompt_geometry_localized(catalog, monkeypatch):
    signed = []

    async def fake_sign(media, *_):
        signed.append(media)
        return []

    monkeypatch.setattr(question_resources, "sign_media", fake_sign)
    user = uuid.uuid4()
    store = InMemoryStore(catalog)
    svc = PracticeService(store, catalog, scripted([]), ServiceConfig())
    additions = [q for q in catalog.questions.values() if q.assets.get("preparation_id") in THIRD_INTAKE_IDS]
    assert len(additions) == 9
    for question in additions:
        ident = question.assets["preparation_id"]
        started = await svc.start(user, question_key=question.key, mode="deep", language="he")
        attempt_id = uuid.UUID(started.id)
        for language in ("he", "en"):
            hidden = await svc.question_resources(user, question.key, attempt_id=attempt_id, language=language)
            assert hidden.reference is None and hidden.technical_material is None and not hidden.solution_revealed
            assert all(m["role"] == "prompt" and m["source_path"].startswith("diagrams/") for m in signed[-1])
            assert all(m.get("language") == language for m in signed[-1])
            if ident in {"PREP-078", "PREP-082"}:
                assert signed[-1], "The counter/track question needs authored geometry before reveal"

        await svc.reveal_reference(user, attempt_id)
        for language in ("he", "en"):
            shown = await svc.question_resources(user, question.key, attempt_id=attempt_id, language=language)
            assert shown.solution_revealed and shown.reference == question.text(language).reference_solution
            assert shown.technical_material["id"] == ident
            assert shown.solution_review.status == "pending_review"
            assert signed[-1] == question_resources.learner_media(question.assets["bank_media"], language)
            assert any(m["role"] == "solution" for m in signed[-1])
            assert all(not m["source_path"].startswith("sources/") for m in signed[-1])
            assert all(m.get("language") in (None, language) for m in signed[-1])
        # Viewing English study resources does not alter the original practice language or create scored evidence.
        assert store.attempts[attempt_id]["row"]["practice_language"] == "he"
    assert not store.metrics


def test_fifth_intake_keeps_the_source_timing_and_window_contracts_distinct(catalog):
    by_id = {q.assets.get("preparation_id"): q for q in catalog.questions.values()}
    asynchronous, synchronous = by_id["PREP-091"], by_id["PREP-004"]
    assert asynchronous.key != synchronous.key
    assert "OUT rises immediately on either input transition" in asynchronous.text("en").prompt
    assert "OUT = In XOR Q" in asynchronous.text("en").reference_solution
    assert "out=Q1 XOR Q2" in synchronous.text("en").reference_solution
    assert "sticky" in asynchronous.text("en").reference_solution
    assert "CDC synchronizer" in asynchronous.text("en").reference_solution

    monitor = by_id["PREP-095"]
    prompt = monitor.text("en").prompt
    assert "at least three of the last ten clock samples" in prompt
    assert "includes the current sample" in prompt and "not a sequence of disjoint ten-cycle blocks" in prompt
    assert "Reset initializes the history to zero" in prompt
    assert "100,000" not in prompt and "100000" not in prompt and "100k" not in prompt.lower()
    assert "actual DUT Y" in monitor.text("en").reference_solution
    assert "sample eleven" in monitor.text("en").reference_solution


@pytest.mark.parametrize("intake_ids,prompt_geometry", [
    (FOURTH_INTAKE_IDS, {"PREP-085": "clock", "PREP-087": "polygon"}),
    (FIFTH_INTAKE_IDS, {"PREP-090": "rope", "PREP-091": "prompt-waveform", "PREP-093": "regions"}),
], ids=["fourth-intake", "fifth-intake"])
async def test_new_intakes_are_bilingual_pending_and_gate_all_solutions(catalog, monkeypatch, intake_ids, prompt_geometry):
    additions = [q for q in catalog.questions.values() if q.assets.get("preparation_id") in intake_ids]
    assert len(additions) == len(intake_ids)
    assert {q.assets["preparation_id"] for q in additions} == intake_ids
    mandatory_material = {"assumptions", "optimality", "verification", "edge_cases", "common_mistakes",
                          "interview_answer", "solution_extensions", "source_ambiguities"}
    signed = []

    async def fake_sign(media, *_):
        signed.append(media)
        return []

    monkeypatch.setattr(question_resources, "sign_media", fake_sign)
    store = InMemoryStore(catalog)
    svc = PracticeService(store, catalog, scripted([]), ServiceConfig())
    user = uuid.uuid4()
    for question in additions:
        ident = question.assets["preparation_id"]
        assert question.status == "trial" and question.reuse_status == "pending_review", ident
        assert not question.reviewed_by and not question.assets["assessment_ready"], ident
        assert question.assets["difficulty_status"] == "unrated", ident
        assert solution_review(question).status == "pending_review", ident
        resource = question.assets["preparation_resource"]
        assert resource["solution_status"] == "proposed" and resource["ai_assisted"], ident
        material = resource["learner_material"]
        assert mandatory_material <= material.keys(), ident
        for field, values in material.items():
            assert set(values) == {"he", "en"}, (ident, field)
            assert all(values[language] not in (None, "", [], {}) for language in ("he", "en")), (ident, field)
            assert not any("\u05d0" <= char <= "\u05ea" for char in json.dumps(values["en"], ensure_ascii=False)), (ident, field)
        assert any(m["source_path"].startswith("sources/") for m in question.assets["bank_media"]), ident
        started = await svc.start(user, question_key=question.key, mode="deep", language="he")
        attempt_id = uuid.UUID(started.id)
        for language in ("he", "en"):
            text = question.text(language)
            assert text.prompt and text.reference_solution and len(text.hints) == len(set(text.hints)) == 3
            assert not text.parity_checked, "A new bilingual solution has no inherited human attestation"
            if language == "en":
                assert not any("\u05d0" <= char <= "\u05ea" for char in text.prompt + text.reference_solution + "".join(text.hints))
            hidden = await svc.question_resources(user, question.key, attempt_id=attempt_id, language=language)
            assert hidden.reference is None and hidden.technical_material is None and not hidden.solution_revealed
            assert all(m["role"] == "prompt" and m["source_path"].startswith("diagrams/") for m in signed[-1])
            assert all(m.get("language") == language for m in signed[-1])
            if ident in prompt_geometry:
                filename = f"{ident.lower()}-{prompt_geometry[ident]}-{language}.png"
                assert any(m["filename"] == filename for m in signed[-1]), (ident, language)
        await svc.reveal_reference(user, attempt_id)
        for language in ("he", "en"):
            shown = await svc.question_resources(user, question.key, attempt_id=attempt_id, language=language)
            assert shown.solution_revealed and shown.reference == question.text(language).reference_solution
            assert shown.technical_material["id"] == ident and shown.solution_review.status == "pending_review"
            assert any(m["role"] == "solution" for m in signed[-1]), ident
            assert signed[-1] == question_resources.learner_media(question.assets["bank_media"], language)
            assert all(not m["source_path"].startswith("sources/") for m in signed[-1])
        assert store.attempts[attempt_id]["row"]["practice_language"] == "he"
    assert not store.metrics
