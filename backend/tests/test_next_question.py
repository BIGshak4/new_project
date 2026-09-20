"""The next suggested question and the subject roll-up: decided from the evaluation, shown right away, kept on refresh."""

from __future__ import annotations

import uuid

import pytest

from app.engine import next_question
from app.engine.catalog import load_catalog
from app.schemas.engine import Band, SkillState
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_practice_hardening import GOOD, SEEDS, WEAK, scripted

MAJORITY = "example-sensor-majority"          # boolean_algebra, difficulty 2
MASKED = "example-masked-equality"            # boolean_algebra, difficulty 3


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def _args(catalog, *, band, states=None, seen=(), language="en"):
    plan = {"boolean_algebra": 3, "combinational_blocks": 3, "binary_arithmetic": 2, "counters": 2}
    weights = {"boolean_algebra": 0.3, "combinational_blocks": 0.4, "binary_arithmetic": 0.2, "counters": 0.1}
    return dict(current=catalog.questions[MAJORITY], band=band, states=states or {},
                candidates=list(catalog.questions.values()), seen=set(seen), required_levels=plan,
                skill_weights=weights, skill_labels=catalog.skill_labels(), language=language)


class TestSuggest:
    def test_weak_stays_on_the_skill_no_harder_than_now(self, catalog):
        s = next_question.suggest(**_args(catalog, band=Band.WEAK))
        assert s is not None and s.why == "reinforce"
        assert catalog.questions[s.key].primary_skill == "boolean_algebra"
        assert s.difficulty <= catalog.questions[MAJORITY].difficulty + 1 and s.key != MAJORITY
        assert "Boolean" in s.reason or "boolean" in s.reason.lower()

    def test_partial_consolidates_on_the_same_skill(self, catalog):
        s = next_question.suggest(**_args(catalog, band=Band.PARTIAL))
        assert s is not None and s.why == "consolidate" and s.skill == "boolean_algebra"

    def test_strong_advances_to_the_heaviest_open_skill(self, catalog):
        s = next_question.suggest(**_args(catalog, band=Band.STRONG))
        assert s is not None and s.why == "explore"                  # nothing practised yet on that skill
        assert s.skill == "combinational_blocks"                      # largest gap x weight
        assert catalog.questions[s.key].primary_skill == "combinational_blocks"

    def test_strong_prefers_a_skill_already_started_as_advance(self, catalog):
        states = {"combinational_blocks": SkillState(key="combinational_blocks", provisional_level=2, turns=3)}
        s = next_question.suggest(**_args(catalog, band=Band.STRONG, states=states))
        assert s is not None and s.why in ("advance", "explore") and s.skill != "boolean_algebra"

    def test_seen_questions_are_skipped_and_none_when_exhausted(self, catalog):
        primary_only = [k for k, q in catalog.questions.items() if q.primary_skill == "boolean_algebra"]
        s = next_question.suggest(**_args(catalog, band=Band.WEAK, seen=primary_only))
        assert s is not None and s.skill == "boolean_algebra"          # a question examining it as a secondary skill
        assert catalog.questions[s.key].primary_skill != "boolean_algebra"
        examines = [k for k, q in catalog.questions.items() if any(link.skill == "boolean_algebra" for link in q.skills)]
        s = next_question.suggest(**_args(catalog, band=Band.WEAK, seen=examines))
        assert s is not None and s.skill != "boolean_algebra"          # falls through to advance
        everything = list(catalog.questions)
        assert next_question.suggest(**_args(catalog, band=Band.WEAK, seen=everything)) is None

    def test_hebrew_reason(self, catalog):
        s = next_question.suggest(**_args(catalog, band=Band.WEAK, language="he"))
        assert s is not None and any("֐" <= ch <= "ת" for ch in s.reason)


class TestThroughTheService:
    async def test_submission_and_attempt_carry_the_suggestion(self, catalog):
        user = uuid.uuid4()
        store = InMemoryStore(catalog)
        svc = PracticeService(store, catalog, scripted([WEAK, GOOD, GOOD]), ServiceConfig())
        view = await svc.start(user, question_key=MAJORITY, mode="quick", language="en", self_confidence=3)
        attempt_id = uuid.UUID(view.id)
        sub, view = await svc.submit(user, attempt_id, "alarm = A ^ B ^ C", idempotency_key="k1")
        assert sub.status == "done" and sub.band == "WEAK"
        assert sub.next_question is not None and sub.next_question.key != MAJORITY
        assert sub.next_question.why == "reinforce" and sub.next_question.subject == "digital_fundamentals"
        assert sub.next_question.title and sub.next_question.reason
        assert view.next_question == sub.next_question

        again = await svc.get(user, attempt_id)                       # a refresh shows the same suggestion
        assert again.next_question == sub.next_question

        started = await svc.start(user, question_key=sub.next_question.key, mode="quick", language="en",
                                  self_confidence=3)
        assert started.question.key == sub.next_question.key          # and it can be started straight away

    async def test_progress_rolls_skills_up_to_subjects(self, catalog):
        user = uuid.uuid4()
        store = InMemoryStore(catalog)
        svc = PracticeService(store, catalog, scripted([GOOD, GOOD, GOOD]), ServiceConfig())
        view = await svc.start(user, question_key=MAJORITY, mode="quick", language="en", self_confidence=3)
        await svc.submit(user, uuid.UUID(view.id), "majority: at least two of three high", idempotency_key="k1")
        progress = await svc.progress(user, language="en")
        assert progress.subjects, "the role plan has subjects"
        by_key = {s.key: s for s in progress.subjects}
        fundamentals = by_key["digital_fundamentals"]
        assert fundamentals.label and fundamentals.skills_total >= 1
        assert fundamentals.bands["STRONG"] == 1 and fundamentals.attempts == 1
        assert fundamentals.skills_started >= 1
        assert set(fundamentals.levels) == {"1", "2", "3", "4", "5"}
        assert 0 < fundamentals.weight <= 1 and fundamentals.questions_available >= 10
        assert sum(s.weight for s in progress.subjects) == pytest.approx(1.0, abs=0.02)
        untouched = [s for s in progress.subjects if s.key != "digital_fundamentals"]
        assert all(s.attempts == 0 and s.bands == {"STRONG": 0, "PARTIAL": 0, "WEAK": 0} for s in untouched)
        assert progress.recent[0]["subject"] == "digital_fundamentals"
