"""Soft skills and the improvement gradient (Shaked, 2026-10-18): backend-only data read from the judge's stored
output. Pure functions on synthetic evidence, then a service flow on the in-memory store."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.engine import soft_skills as ss
from app.engine.catalog import load_catalog
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.conftest import make_evaluation
from tests.test_practice_hardening import GOOD, SEEDS, scripted

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
USER = uuid.uuid4()


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def ev(days_ago: float, *, archetype="design", skill="counters", flags=(), **scores) -> ss.Evidence:
    base = {"correctness": 0.7, "depth": 0.6, "clarity": 0.6, "structure": 0.6, "tradeoff_reasoning": 0.5,
            "risk_awareness": 0.5, "hedging_ratio": 0.2, "behavior_signals": []}
    base.update(scores)
    return ss.Evidence(at=NOW - timedelta(days=days_ago), evaluation=base, flags=list(flags), archetype=archetype,
                       primary_skill=skill)


class TestPerAnswerScores:
    def test_each_skill_reads_its_own_dimension_and_only_the_relevant_questions(self):
        design = ev(1, structure=0.8, clarity=0.9, tradeoff_reasoning=0.7, risk_awareness=0.4)
        conceptual = ev(1, archetype="conceptual", structure=0.3)
        assert ss.answer_score("structured_explanation", design) == 0.8
        assert ss.answer_score("clear_communication", design) == 0.9
        assert ss.answer_score("tradeoff_reasoning", design) == 0.7
        assert ss.answer_score("tradeoff_reasoning", conceptual) is None            # no trade-off to reason about
        assert ss.answer_score("edge_case_attention", design) == 0.4
        assert ss.answer_score("edge_case_attention", conceptual) is None
        assert ss.answer_score("analytical_reasoning", design) is None               # not a reasoning question
        puzzle = ev(1, archetype="conceptual", skill="estimation_sanity_checks", correctness=0.9, depth=0.7)
        assert ss.answer_score("analytical_reasoning", puzzle) == pytest.approx(0.8)
        assert ss.answer_score("analytical_reasoning", ev(1, archetype="debugging")) == pytest.approx(0.65)

    def test_the_behaviour_tags_move_the_scores(self):
        careful = ev(1, risk_awareness=0.5, behavior_signals=["considered_edge_cases", "stated_assumptions"])
        careless = ev(1, risk_awareness=0.5, behavior_signals=["ignored_edge_cases", "jumped_to_implementation"])
        assert ss.answer_score("edge_case_attention", careful) == pytest.approx(0.65)
        assert ss.answer_score("edge_case_attention", careless) == pytest.approx(0.35)
        assert ss.answer_score("problem_solving_habits", careful) == 1.0
        assert ss.answer_score("problem_solving_habits", careless) == 0.0
        assert ss.answer_score("problem_solving_habits", ev(1)) == 0.5                 # nothing shown: neutral

    def test_calibration_rewards_commitment_when_right_and_hedging_when_wrong(self):
        assert ss.answer_score("calibration", ev(1, correctness=0.9, hedging_ratio=0.0)) == 1.0
        assert ss.answer_score("calibration", ev(1, correctness=0.9, hedging_ratio=1.0)) == pytest.approx(0.4)
        assert ss.answer_score("calibration", ev(1, correctness=0.2, hedging_ratio=0.0)) == pytest.approx(0.3)
        assert ss.answer_score("calibration", ev(1, correctness=0.2, hedging_ratio=1.0)) == pytest.approx(0.7)
        assert ss.answer_score("calibration", ev(1, correctness=0.2, behavior_signals=["overconfident_wrong"])) == 0.1

    def test_an_unrelated_or_empty_answer_says_nothing(self):
        for skill in ss.SOFT_SKILLS:
            assert ss.answer_score(skill, ev(1, flags=["off_topic"])) is None
            assert ss.answer_score(skill, ev(1, flags=["empty_answer"])) is None


class TestLevelsAndGradient:
    def test_too_few_answers_give_no_level_and_too_early(self):
        rows = ss.assess([ev(d, structure=0.9) for d in range(4)], NOW)
        structured = next(r for r in rows if r.key == "structured_explanation")
        assert structured.answers == 4 and structured.level is None and structured.improvement == "too_early"

    def test_a_rising_candidate_reads_improving_and_a_flat_one_steady(self):
        rising = [ev(28 - d, structure=0.3 + d * 0.02) for d in range(0, 28, 2)]            # 0.3 -> 0.82 over four weeks
        flat = [ev(28 - d, structure=0.6) for d in range(0, 28, 2)]
        r = next(x for x in ss.assess(rising, NOW) if x.key == "structured_explanation")
        f = next(x for x in ss.assess(flat, NOW) if x.key == "structured_explanation")
        assert r.improvement == "improving_quickly" and r.slope_per_week > ss.SLOPE_QUICK
        assert f.improvement == "steady" and f.slope_per_week == 0
        assert r.level_rank == 4 and f.level_rank == 4 and r.mean > f.mean               # recent answers weigh more
        slipping = [ev(28 - d, clarity=0.9 - d * 0.02) for d in range(0, 28, 2)]
        s = next(x for x in ss.assess(slipping, NOW) if x.key == "clear_communication")
        assert s.improvement == "slipping"

    def test_recent_answers_weigh_more_and_old_ones_fall_out_of_the_level(self):
        old_good = [ev(60 + d, structure=0.9) for d in range(6)]                              # beyond the 49-day window
        recent_weak = [ev(d, structure=0.35) for d in range(6)]
        r = next(x for x in ss.assess(old_good + recent_weak, NOW) if x.key == "structured_explanation")
        assert r.answers == 6 and r.mean == pytest.approx(0.35, abs=0.01) and r.level_rank == 2

    def test_the_hard_skill_gradient_reads_the_level_history(self):
        history = {"counters": [{"level": 1 + i // 2, "at": (NOW - timedelta(days=30 - 3 * i)).isoformat()} for i in range(10)],
                   "truth_tables": [{"level": 3, "at": (NOW - timedelta(days=1)).isoformat()}]}
        hard = ss.hard_skill_gradient(history, NOW)
        assert hard["counters"]["improvement"] in ("improving", "improving_quickly") and hard["counters"]["slope_per_week"] > 0
        assert hard["truth_tables"]["improvement"] == "too_early"
        soft = ss.assess([ev(28 - d, structure=0.3 + d * 0.02) for d in range(0, 28, 2)], NOW)
        overall = ss.overall_improvement(soft, hard, {"counters": 0.05, "truth_tables": 0.03})
        assert overall["improvement"] in ("improving", "improving_quickly") and overall["skills_judged"] >= 2
        assert ss.overall_improvement([], {}, {})["improvement"] == "too_early"

    def test_every_word_exists_in_both_languages(self):
        assert set(ss.IMPROVEMENT_WORDS["he"]) == set(ss.IMPROVEMENT_WORDS["en"]) == {"too_early", "slipping", "steady", "improving", "improving_quickly"}
        assert len(ss.LEVEL_WORDS["he"]) == len(ss.LEVEL_WORDS["en"]) == 5
        assert all(set(v) == {"en", "he"} for v in ss.SOFT_SKILLS.values())


class TestOnTheService:
    async def test_the_reading_comes_from_stored_answers_and_touches_no_route(self, catalog):
        evaluations = [make_evaluation(correctness=0.8, depth=0.7, structure=0.4 + i * 0.1, clarity=0.7,
                                       behavior_signals=["stated_assumptions"] if i % 2 else []).model_dump() for i in range(6)]
        store = InMemoryStore(catalog)
        svc = PracticeService(store, catalog, scripted(evaluations + [GOOD] * 6), ServiceConfig(suggest_reviewed_only=False))
        keys = [k for k, q in catalog.questions.items() if q.archetype.value == "design"][:6] or list(catalog.questions)[:6]
        for i, key in enumerate(keys):
            view = await svc.start(USER, question_key=key, mode="quick", language="en")
            await svc.submit(USER, uuid.UUID(view.id), "a careful answer with assumptions stated", idempotency_key=f"k{i}")
        result = await svc.soft_skills(USER)
        assert result["answers_read"] == 6
        by_key = {s["key"]: s for s in result["soft_skills"]}
        assert set(by_key) == set(ss.SOFT_SKILLS)
        structured = by_key["structured_explanation"]
        assert structured["answers"] == 6 and structured["level"] is not None and structured["improvement"] == "too_early"  # same day
        assert by_key["problem_solving_habits"]["mean"] == pytest.approx(0.75, abs=0.01)         # 3 of 6 stated assumptions
        assert "overall" in result and result["overall"]["improvement"] == "too_early"
        # nothing of it on the API: the progress view has no such field
        progress = await svc.progress(USER, language="en")
        assert not hasattr(progress, "soft_skills")
