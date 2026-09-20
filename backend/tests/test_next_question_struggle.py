"""The next question answers what was hard: a recognised mistake picks the skill it undermines and explains itself."""

from __future__ import annotations

import uuid

import pytest

from app.engine import next_question
from app.engine.catalog import load_catalog
from app.engine.next_question import Struggle
from app.schemas.engine import Band
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.conftest import make_evaluation
from tests.test_practice_hardening import GOOD, SEEDS, WEAK, scripted

MAJORITY = "example-sensor-majority"          # boolean_algebra (primary) + truth_tables (secondary), difficulty 2


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def _args(catalog, **over):
    base = dict(current=catalog.questions[MAJORITY], band=Band.WEAK, states={}, candidates=list(catalog.questions.values()),
                seen=set(), required_levels={"boolean_algebra": 3, "truth_tables": 2, "combinational_blocks": 3},
                skill_weights={"boolean_algebra": 0.3, "truth_tables": 0.2, "combinational_blocks": 0.4},
                skill_labels=catalog.skill_labels(), language="en")
    return {**base, **over}


class TestStruggles:
    def test_a_core_mistake_on_the_main_skill_explains_itself(self, catalog):
        s = next_question.suggest(**_args(catalog, struggles=[
            Struggle("xor_confused_with_majority", "boolean_algebra", "XOR is treated as 'more than one input is 1'", core=True)]))
        assert s is not None and s.why == "reinforce" and s.skill == "boolean_algebra"
        assert s.focus == "XOR is treated as 'more than one input is 1'."
        assert "Boolean" in s.reason or "boolean" in s.reason.lower()
        assert catalog.questions[s.key].primary_skill == "boolean_algebra" and s.key != MAJORITY

    def test_a_mistake_on_the_secondary_skill_leads_to_a_question_that_examines_it(self, catalog):
        s = next_question.suggest(**_args(catalog, band=Band.PARTIAL, struggles=[
            Struggle("exactly_two_instead_of_at_least_two", "truth_tables", "Row 111 is given output 0.")]))
        assert s is not None and s.skill == "truth_tables"
        assert any(link.skill == "truth_tables" for link in catalog.questions[s.key].skills)
        assert s.focus == "Row 111 is given output 0."

    def test_core_mistakes_outrank_minor_ones(self, catalog):
        s = next_question.suggest(**_args(catalog, struggles=[
            Struggle("exactly_two_instead_of_at_least_two", "truth_tables", "Row 111 is given output 0."),
            Struggle("xor_confused_with_majority", "boolean_algebra", "XOR is not majority.", core=True)]))
        assert s is not None and s.skill == "boolean_algebra" and s.focus == "XOR is not majority."

    def test_empty_explanations_are_ignored_and_the_band_decides(self, catalog):
        s = next_question.suggest(**_args(catalog, struggles=[Struggle("x", "boolean_algebra", "   ")]))
        assert s is not None and s.focus is None and s.why == "reinforce"

    def test_a_weak_follow_up_after_a_strong_main_answer_still_reinforces(self, catalog):
        s = next_question.suggest(**_args(catalog, band=Band.STRONG, follow_up_bands=[Band.WEAK]))
        assert s is not None and s.why == "reinforce" and s.skill == "boolean_algebra"
        s2 = next_question.suggest(**_args(catalog, band=Band.STRONG, follow_up_bands=[Band.STRONG]))
        assert s2 is not None and s2.why in ("advance", "explore")

    def test_hebrew_struggle_reason(self, catalog):
        s = next_question.suggest(**_args(catalog, language="he", struggles=[
            Struggle("xor_confused_with_majority", "boolean_algebra", "XOR מטופל כרוב", core=True)]))
        assert s is not None and any("֐" <= ch <= "ת" for ch in s.reason) and s.focus == "XOR מטופל כרוב."


class TestThroughTheService:
    async def test_recognised_mistake_becomes_the_focus_of_the_suggestion(self, catalog):
        user = uuid.uuid4()
        store = InMemoryStore(catalog)
        # WEAK carries the core misconception xor_confused_with_majority; follow-ups answered well
        svc = PracticeService(store, catalog, scripted([WEAK, GOOD, GOOD]), ServiceConfig())
        view = await svc.start(user, question_key=MAJORITY, mode="deep", language="en", self_confidence=3)
        aid = uuid.UUID(view.id)
        sub, view = await svc.submit(user, aid, "alarm = A ^ B ^ C", idempotency_key="k1")
        assert sub.band == "WEAK" and sub.next_question is not None
        assert sub.next_question.focus and "XOR" in sub.next_question.focus
        assert sub.next_question.skill == "boolean_algebra" and sub.next_question.why == "reinforce"
        turns = 0
        while view.pending_follow_up is not None and turns < 3:
            _, view = await svc.submit(user, aid, "majority means at least two of three", idempotency_key=f"f{turns}",
                                       follow_up_turn=view.pending_follow_up.turn)
            turns += 1
        assert view.status == "done"
        # the mistake stays on record for the attempt: the final suggestion still answers it
        assert view.next_question is not None and view.next_question.focus and "XOR" in view.next_question.focus

    async def test_a_strong_follow_up_does_not_erase_a_partial_main_answer(self, catalog):
        user = uuid.uuid4()
        store = InMemoryStore(catalog)
        partial = make_evaluation(correctness=0.6, depth=0.5, key_points_missed=["no truth table"]).model_dump()
        svc = PracticeService(store, catalog, scripted([partial, GOOD]), ServiceConfig())
        view = await svc.start(user, question_key=MAJORITY, mode="deep", language="en", self_confidence=3)
        aid = uuid.UUID(view.id)
        sub, view = await svc.submit(user, aid, "alarm = AB + BC + AC", idempotency_key="k1")
        assert sub.band == "PARTIAL" and view.pending_follow_up is not None
        fsub, view = await svc.submit(user, aid, "the table has 1 in rows 011, 101, 110, 111", idempotency_key="f1",
                                      follow_up_turn=view.pending_follow_up.turn)
        assert fsub.band == "STRONG" and view.status == "done"
        # the main answer was only partial: consolidate the same skill, do not jump to a new one
        assert view.next_question is not None and view.next_question.why == "consolidate"
        assert view.next_question.skill == "boolean_algebra"

    async def test_secondary_skill_mistake_from_the_bank_texts(self, catalog):
        user = uuid.uuid4()
        store = InMemoryStore(catalog)
        partial = make_evaluation(correctness=0.6, depth=0.5, misconceptions=["exactly_two_instead_of_at_least_two"]).model_dump()
        svc = PracticeService(store, catalog, scripted([partial, GOOD, GOOD]), ServiceConfig())
        view = await svc.start(user, question_key=MAJORITY, mode="quick", language="he", self_confidence=3)
        sub, _ = await svc.submit(user, uuid.UUID(view.id), "alarm = AB + BC", idempotency_key="k1")
        assert sub.next_question is not None and sub.next_question.skill == "truth_tables"
        assert sub.next_question.focus and any("֐" <= ch <= "ת" for ch in sub.next_question.focus)  # Hebrew bank text
