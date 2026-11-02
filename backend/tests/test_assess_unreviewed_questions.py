"""Shaked, 2026-11-02: "change all the questions so they act like normal questions; they just need the last stamp".
ASSESS_UNREVIEWED_QUESTIONS makes a question loaded with assessment_ready=false behave like any other: follow-ups,
evidence, XP and coins; the review stamp stays the question's status."""

from __future__ import annotations

import pytest

from app.config import Settings
from app.engine import bank
from app.engine.catalog import load_catalog
from app.runtime import build_runtime
from tests.test_practice_hardening import SEEDS, WEAK, attempt_for, scripted

STUDY_ONLY = "prep-eight-bit-popcount-adders"          # one of Harel's generated questions: assessment_ready false in the seed


async def no_images(question):
    return []                                    # every generated question carries a figure; the engine wants a fetcher


@pytest.fixture
def switch(monkeypatch):
    def set_to(value: bool):
        monkeypatch.setattr(bank, "ASSESS_UNREVIEWED_QUESTIONS", value)
    return set_to


def test_apply_readiness_only_flips_false_and_only_when_on(switch):
    switch(False)
    assert bank.apply_readiness({"assessment_ready": False})["assessment_ready"] is False
    switch(True)
    assert bank.apply_readiness({"assessment_ready": False})["assessment_ready"] is True
    assert bank.apply_readiness({})  == {}                                      # unset stays unset (treated as ready already)
    assert bank.apply_readiness({"assessment_ready": True})["assessment_ready"] is True


async def test_the_seed_question_is_study_only_by_default_and_gets_a_follow_up_with_the_switch(switch):
    switch(False)
    catalog = load_catalog(SEEDS)
    assert catalog.questions[STUDY_ONLY].assets["assessment_ready"] is False
    # a weak answer: on a reviewed question the controller would open a hint follow-up (a strong answer at the
    # difficulty ceiling resolves without one, which is the normal rule, not this switch)
    attempt, _ = attempt_for(catalog, scripted([WEAK]), key=STUDY_ONLY, question_image_fetcher=no_images)
    outcome = await attempt.submit("a weak answer", idempotency_key="k")
    assert outcome.band is not None, outcome.flags
    assert attempt.follow_up_turns == [] and outcome.evidence_weight == 0.0

    switch(True)
    catalog = load_catalog(SEEDS)
    bank.apply_readiness(catalog.questions[STUDY_ONLY].assets)
    attempt, _ = attempt_for(catalog, scripted([WEAK]), key=STUDY_ONLY, question_image_fetcher=no_images)
    outcome = await attempt.submit("a weak answer", idempotency_key="k")
    assert outcome.band is not None and outcome.evidence_weight > 0
    assert len(attempt.follow_up_turns) == 1 and attempt.follow_up_turns[0]["action"] in ("HINT", "STEP_BACK", "HOLD")


def test_the_runtime_applies_the_setting_to_the_seed_catalog(switch):
    switch(False)
    off = build_runtime(Settings(_env_file=None, seeds_dir=SEEDS, llm_provider="scripted"))
    assert off.catalog.questions[STUDY_ONLY].assets["assessment_ready"] is False and bank.ASSESS_UNREVIEWED_QUESTIONS is False
    on = build_runtime(Settings(_env_file=None, seeds_dir=SEEDS, llm_provider="scripted", assess_unreviewed_questions=True))
    assert on.catalog.questions[STUDY_ONLY].assets["assessment_ready"] is True and bank.ASSESS_UNREVIEWED_QUESTIONS is True
