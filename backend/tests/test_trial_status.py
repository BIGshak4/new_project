"""The "on trial" question state: served like published, usable by the coach and the interview, badged."""

from __future__ import annotations

import copy
import uuid

import pytest

from app.engine import bank
from app.engine.catalog import load_catalog
from app.repo.questions import LoadedQuestion, summary
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_interview_service import Clock, interviewer
from tests.test_practice_hardening import GOOD, SEEDS, WEAK, scripted

MAJORITY = "example-sensor-majority"
TRIAL_KEYS = (MAJORITY, "example-masked-equality", "example-nand-only-enable", "example-enabled-decoder", "example-mod-six-counter")


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


@pytest.fixture(scope="module")
def trial_catalog(catalog):
    """The seed catalog with five questions moved to 'trial', as the founders would do with the status script."""
    trial = copy.copy(catalog)
    trial.questions = {k: (q.model_copy(update={"status": "trial"}) if k in TRIAL_KEYS else q) for k, q in catalog.questions.items()}
    return trial


def test_summary_flags_and_bank_rules(trial_catalog):
    q = trial_catalog.questions[MAJORITY]
    s = summary(LoadedQuestion(id=uuid.uuid4(), question=q, version=1), "en")
    assert s.status == "trial" and s.reviewed is True and s.trial is True
    other = summary(LoadedQuestion(id=uuid.uuid4(), question=trial_catalog.questions["example-count-set-bits"], version=1), "en")
    assert other.reviewed is False and other.trial is False
    # served without the development switch, in production rules; parity is checked live while on trial
    assert bank._servable(q, mode=q.practice_modes[0], language="en", allow_in_review=False, require_parity=True)
    assert not bank._servable(trial_catalog.questions["example-count-set-bits"], mode="deep", language="en",
                              allow_in_review=False, require_parity=True)
    coverage = bank.coverage_by_skill(list(trial_catalog.questions.values()), language="en", allow_in_review=False,
                                      require_parity=True)
    assert "boolean_algebra" in coverage and "bit_manipulation" not in coverage


async def test_the_coach_suggests_trial_questions_under_the_default_rule(trial_catalog):
    user = uuid.uuid4()
    store = InMemoryStore(trial_catalog, allow_in_review=False)         # production: no in-review content
    svc = PracticeService(store, trial_catalog, scripted([WEAK, GOOD, GOOD]), ServiceConfig())   # suggest_reviewed_only=True
    listed = await svc.list_questions(language="en")
    assert {q.key for q in listed} == set(TRIAL_KEYS) and all(q.trial for q in listed)
    view = await svc.start(user, question_key=MAJORITY, mode="quick", language="en", self_confidence=3)
    sub, _ = await svc.submit(user, uuid.UUID(view.id), "alarm = A ^ B ^ C", idempotency_key="k1")
    assert sub.band == "WEAK" and sub.next_question is not None
    assert sub.next_question.key in TRIAL_KEYS and sub.next_question.key != MAJORITY


async def test_the_interview_runs_on_trial_questions_under_the_default_rule(trial_catalog):
    store = InMemoryStore(trial_catalog, allow_in_review=False)
    svc = InterviewService(store, trial_catalog, interviewer([GOOD, WEAK]), InterviewConfig())       # reviewed_only=True
    svc.clock = Clock(step_min=3)
    user = uuid.uuid4()
    view = await svc.start(user, duration_min=20, language="en")
    covered = {trial_catalog.questions[k].primary_skill for k in TRIAL_KEYS}
    assert view.current_turn is not None and view.current_turn.question_key in TRIAL_KEYS and view.current_turn.trial
    assert {p.skill for p in view.plan} <= covered
    asked = []
    while view.status == "in_progress" and view.current_turn is not None and len(asked) < 10:
        asked.append(view.current_turn.question_key)
        svc.clock.advance()
        _, view = await svc.answer(user, uuid.UUID(view.id), view.current_turn.index, "answer", idempotency_key=f"k{len(asked)}")
    assert set(asked) <= set(TRIAL_KEYS) and len(set(asked)) == len(asked)
    assert view.status == "completed"
