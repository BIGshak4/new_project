"""Localized study reads keep the existing ownership/reveal boundary and never change an attempt."""

from __future__ import annotations

import copy
import uuid

import pytest

from app.api.errors import ApiError
from app.engine.catalog import load_catalog
from app.services import question_resources
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_practice_hardening import SEEDS, scripted


@pytest.fixture
def resources_service(monkeypatch):
    catalog = load_catalog(SEEDS)
    store = InMemoryStore(catalog)
    provider = scripted([])
    service = PracticeService(store, catalog, provider, ServiceConfig(daily_attempt_limit=1000))
    signed = []

    async def fake_sign(media, *_):
        signed.append(media)
        return []

    monkeypatch.setattr(question_resources, "sign_media", fake_sign)
    return service, store, provider, signed


async def test_localized_reference_works_for_every_bank_question_without_changing_attempts(resources_service, monkeypatch):
    service, store, provider, _ = resources_service
    user = uuid.uuid4()

    async def no_feedback_resume(*_):
        raise AssertionError("A study-material read must not load the attempt through get() or resume feedback")

    monkeypatch.setattr(service, "get", no_feedback_resume)
    for question in service.catalog.questions.values():
        attempt = await service.start(user, question_key=question.key, language="he")
        attempt_id = uuid.UUID(attempt.id)
        await service.reveal_reference(user, attempt_id)
        before = copy.deepcopy(store.attempts[attempt_id])
        profiles = copy.deepcopy(store.profiles)
        for language in ("en", "he", "en"):
            resources = await service.question_resources(user, question.key, attempt_id=attempt_id, language=language)
            assert resources.solution_revealed, question.key
            assert resources.reference == question.text(language).reference_solution, question.key
            assert resources.language == language
        default = await service.question_resources(user, question.key, attempt_id=attempt_id)
        assert default.language == "he" and default.reference == question.text("he").reference_solution
        assert store.attempts[attempt_id] == before
        assert store.profiles == profiles
    assert not provider.requests and not store.metrics and not store.usage


async def test_reference_requires_owned_matching_revealed_attempt_in_both_languages(resources_service):
    service, _, _, signed = resources_service
    user, stranger = uuid.uuid4(), uuid.uuid4()
    question = service.catalog.questions["example-sensor-majority"]
    attempt = await service.start(user, question_key=question.key, language="en")
    attempt_id = uuid.UUID(attempt.id)
    for language in ("he", "en"):
        for requested_attempt in (None, attempt_id):
            hidden = await service.question_resources(user, question.key, attempt_id=requested_attempt, language=language)
            assert hidden.reference is None and hidden.technical_material is None and not hidden.solution_revealed
            assert all(media["role"] == "prompt" for media in signed[-1])
    await service.reveal_reference(user, attempt_id)
    for caller, key, requested_attempt in ((stranger, question.key, attempt_id),
                                            (user, "example-mod-six-counter", attempt_id),
                                            (user, question.key, uuid.uuid4())):
        signed_before = len(signed)
        with pytest.raises(ApiError) as denied:
            await service.question_resources(caller, key, attempt_id=requested_attempt, language="he")
        assert denied.value.code == "not_found"
        assert len(signed) == signed_before


async def test_resource_language_reports_fallback_and_does_not_bypass_question_visibility(resources_service):
    service, store, _, _ = resources_service
    question = service.catalog.questions["example-sensor-majority"]
    question.translations.pop("he")
    user = uuid.uuid4()
    attempt = await service.start(user, question_key=question.key, language="en")
    attempt_id = uuid.UUID(attempt.id)
    await service.reveal_reference(user, attempt_id)
    resources = await service.question_resources(user, question.key, attempt_id=attempt_id, language="he")
    assert resources.language == "en" and resources.reference == question.text("en").reference_solution
    question.status = "in_review"
    store.allow_in_review = False
    with pytest.raises(ApiError) as unavailable:
        await service.question_resources(user, question.key, attempt_id=attempt_id, language="en")
    assert unavailable.value.code == "not_found"


async def test_resource_language_rejects_unsupported_language(resources_service):
    service, _, _, _ = resources_service
    with pytest.raises(ApiError) as invalid:
        await service.question_resources(uuid.uuid4(), "example-sensor-majority", language="fr")
    assert invalid.value.code == "validation"
