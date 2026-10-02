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
from app.repo.questions import LoadedQuestion, summary
from app.services import question_resources
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_practice_hardening import GOOD, SEEDS, scripted

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def catalog():
    return load_catalog(SEEDS)


def test_compilation_preserves_every_question_and_all_original_images(catalog):
    source = json.loads((ROOT / "interview_preparation/questions.json").read_text(encoding="utf-8-sig"))
    manifest = json.loads((SEEDS / "preparation_uploads.json").read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("prep_builder", ROOT / "backend/scripts/build_preparation_bank.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    built, uploads = builder.load()
    assert built == json.loads((SEEDS / "questions/preparation_bank.json").read_text(encoding="utf-8"))
    assert uploads == manifest["files"]
    assert len(source["questions"]) == len(built) == 37
    for q in built:
        for media in q["assets"]["bank_media"]:
            if any(word in media["filename"] for word in ("external-answer", "clarification", "style-reference", "course-adder-summary")):
                assert media["role"] == "solution", "An explanation screenshot must never leak before reference reveal"
    assert len(catalog.questions) == 67
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
            assert q.text(lang).prompt == original["translations"][lang]["prompt"]
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
    assert signed[-1] == question_resources.learner_media(q.assets["bank_media"])
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
    assert len(archive) == 50
    # No credentials or network needed: the boundary applies before signing.
    assert await question_resources.sign_media(archive, "", "") == []
    all_media = [m for q in catalog.questions.values() for m in q.assets.get("bank_media", [])]
    retained = question_resources.learner_media(all_media)
    assert retained and len(retained) + len(archive) == len(all_media)
    assert all(m["source_path"].startswith(("diagrams/", "solutions/")) for m in retained)
