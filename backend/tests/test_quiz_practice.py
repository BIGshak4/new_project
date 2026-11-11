"""Real game-bank practice is private, answer-safe, versioned and has no rewards."""

from __future__ import annotations

import base64
import json
from dataclasses import replace

import pytest

from app.api.errors import ApiError
from app.main import app
from app.services.quiz_practice import ROUND_TTL, QuizPractice
from tests import test_duels
from tests.authtools import make_token
from tests.test_duels import A, B, service

catalog = test_duels.catalog
client = test_duels.client


def test_real_approved_question_and_correctness_without_game_side_effects(catalog):
    svc, store, _ = service(catalog)
    for language in ("he", "en"):
        round_ = svc.practice.start(A, language)
        question = svc.quiz[round_["question"]["key"]]
        assert question.status == "approved"
        assert round_["question"]["prompt"] == question.prompt[language]
        assert round_["question"]["choices"] == [choice[language] for choice in question.choices]
        assert "correct" not in round_["question"] and "explanation" not in round_["question"]
        claims = json.loads(base64.urlsafe_b64decode(round_["round_token"].split(".")[0]))
        assert "correct" not in claims and "explanation" not in claims
        wrong = svc.practice.answer(A, round_["round_token"], (question.correct + 1) % 4)
        assert wrong["correct"] is False and wrong["correct_index"] == question.correct
        right = svc.practice.answer(A, round_["round_token"], question.correct)
        assert right["correct"] is True and right["explanation"] == question.explanation[language]
    assert store.duels == {} and store.coin_ledger == [] and store.attempts == {}


def test_round_is_owner_bound_and_tampering_or_expiry_does_not_reveal_answers(catalog):
    svc, _, clock = service(catalog)
    round_ = svc.practice.start(A, "he")
    with pytest.raises(ApiError) as other:
        svc.practice.answer(B, round_["round_token"], 0)
    assert other.value.status == 403
    for token in ("bad", round_["round_token"] + "0", "é." + "0" * 64):
        with pytest.raises(ApiError) as tampered:
            svc.practice.answer(A, token, 0)
        assert tampered.value.code == "practice_round_expired"
    clock.advance(ROUND_TTL.total_seconds())
    with pytest.raises(ApiError) as expired:
        svc.practice.answer(A, round_["round_token"], 0)
    assert expired.value.code == "practice_round_expired"


@pytest.mark.parametrize("change", [{"correct": 1}, {"status": "draft"}, {"prompt": {"he": "updated", "en": "updated"}}])
def test_bank_edits_expire_open_rounds(catalog, change):
    svc, _, _ = service(catalog)
    round_ = svc.practice.start(A, "en")
    key = round_["question"]["key"]
    question = svc.quiz[key]
    if "correct" in change:
        change = {"correct": (question.correct + 1) % 4}
    svc.quiz[key] = replace(question, **change)
    with pytest.raises(ApiError) as stale:
        svc.practice.answer(A, round_["round_token"], 0)
    assert stale.value.code == "practice_round_expired"


def test_only_approved_complete_source_groups_are_used_and_workers_share_tokens(catalog):
    svc, _, _ = service(catalog)
    svc.practice = QuizPractice(svc, secret="a-test-service-key")
    round_ = svc.practice.start(A, "en")
    another_worker = QuizPractice(svc, secret="a-test-service-key")
    assert another_worker.answer(A, round_["round_token"], 0)["question"] == round_["question"]
    svc.quiz = {key: replace(q, status="draft") for key, q in svc.quiz.items()}
    with pytest.raises(ApiError) as empty:
        svc.practice.start(A, "en")
    assert empty.value.code == "no_reviewed_questions"


async def test_http_auth_answer_boundary_validation_and_no_store(client):
    assert (await client.get("/v1/duels/practice")).status_code == 401
    _, token_a = make_token(email="a@example.com")
    headers = {"Authorization": f"Bearer {token_a}"}
    response = await client.get("/v1/duels/practice?language=en", headers=headers)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "private, no-store"
    body = response.json()
    assert set(body["question"]) == {"index", "key", "source_key", "variant", "prompt", "choices"}
    correct = app.state.runtime.duels.quiz[body["question"]["key"]].correct
    payload = {"round_token": body["round_token"], "choice": correct}
    assert (await client.post("/v1/duels/practice/answer", json=payload)).status_code == 401
    _, token_b = make_token(email="b@example.com")
    assert (await client.post("/v1/duels/practice/answer", json=payload,
                              headers={"Authorization": f"Bearer {token_b}"})).status_code == 403
    for choice in (-1, 4, "1", True):
        assert (await client.post("/v1/duels/practice/answer", json={**payload, "choice": choice}, headers=headers)).status_code == 422
    result = await client.post("/v1/duels/practice/answer", json=payload, headers=headers)
    assert result.status_code == 200 and result.json()["correct"] is True
    assert result.headers["cache-control"] == "private, no-store"
    assert (await client.get("/v1/duels/practice?language=fr", headers=headers)).status_code == 422
    assert app.state.runtime.store.duels == {} and app.state.runtime.store.coin_ledger == []
