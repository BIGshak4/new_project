"""XP: the motivation layer. Pure arithmetic, the per-skill split, streaks, and the proof that the engine's
bands and levels are the same with and without it (XP only reads what the engine stored)."""

from __future__ import annotations

import ast
import uuid
from datetime import date, timedelta
from pathlib import Path

import pytest

from app.engine import xp
from app.engine.catalog import load_catalog
from app.services import practice_service
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_practice_hardening import GOOD, SEEDS, scripted

USER = uuid.uuid4()
Q = "example-sensor-majority"
TODAY = date(2026, 9, 25)


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


class TestTheArithmetic:
    @pytest.mark.parametrize("band, difficulty, expected", [
        ("STRONG", 1, 20), ("PARTIAL", 1, 10), ("WEAK", 1, 4),
        ("STRONG", 10, 40), ("PARTIAL", 10, 20), ("WEAK", 10, 8),        # difficulty 10 doubles
        ("STRONG", 5, 29),                                                 # 20 * (1 + 4/9) = 28.9
    ])
    def test_band_times_difficulty(self, band, difficulty, expected):
        assert xp.answer_xp(band, difficulty=difficulty) == expected

    @pytest.mark.parametrize("hints, expected", [(0, 20), (1, 16), (2, 12), (3, 8), (4, 8), (9, 8)])
    def test_hints_take_a_fifth_each_down_to_the_floor(self, hints, expected):
        assert xp.answer_xp("STRONG", difficulty=1, hints_seen=hints) == expected

    def test_reference_follow_up_and_interview_factors(self):
        assert xp.answer_xp("STRONG", difficulty=1, reference_seen=True) == 5
        assert xp.answer_xp("STRONG", difficulty=1, follow_up=True) == 10
        assert xp.answer_xp("STRONG", difficulty=1, interview=True) == 30
        assert xp.answer_xp("PARTIAL", difficulty=10, hints_seen=1, interview=True) == 24      # 10*2*0.8*1.5

    def test_any_scored_answer_is_worth_at_least_one(self):
        assert xp.answer_xp("WEAK", difficulty=1, reference_seen=True) == 1                    # 4 * 0.25 = 1
        assert xp.answer_xp("WEAK", difficulty=1, hints_seen=3, reference_seen=True, follow_up=True) == 1   # 0.2 -> 1

    def test_unscored_answers_earn_nothing(self):
        assert xp.answer_xp(None, difficulty=5) == 0
        assert xp.answer_xp("", difficulty=5) == 0
        assert xp.answer_xp("UNKNOWN", difficulty=5) == 0

    def test_difficulty_is_clamped_to_the_bank_range(self):
        assert xp.answer_xp("STRONG", difficulty=0) == 20 and xp.answer_xp("STRONG", difficulty=99) == 40


class TestThePerSkillSplit:
    def test_split_by_link_weights_adds_up_exactly(self):
        assert xp.split_by_skill(15, [("a", 0.6), ("b", 0.4)]) == {"a": 9, "b": 6}
        parts = xp.split_by_skill(20, [("a", 1 / 3), ("b", 1 / 3), ("c", 1 / 3)])
        assert sum(parts.values()) == 20 and sorted(parts.values()) == [6, 7, 7]

    def test_one_skill_takes_everything_and_no_links_take_nothing(self):
        assert xp.split_by_skill(7, [("only", 1.0)]) == {"only": 7}
        assert xp.split_by_skill(7, []) == {} and xp.split_by_skill(0, [("a", 1.0)]) == {}


class TestTheStreak:
    def test_today_yesterday_and_the_day_before(self):
        days = [TODAY, TODAY - timedelta(days=1), TODAY - timedelta(days=2)]
        assert xp.streak_days(days, TODAY) == 3

    def test_today_not_yet_practised_does_not_break_it(self):
        assert xp.streak_days([TODAY - timedelta(days=1), TODAY - timedelta(days=2)], TODAY) == 2

    def test_a_gap_ends_it(self):
        assert xp.streak_days([TODAY - timedelta(days=2), TODAY - timedelta(days=3)], TODAY) == 0
        assert xp.streak_days([TODAY, TODAY - timedelta(days=2)], TODAY) == 1

    def test_today_only_and_nothing(self):
        assert xp.streak_days(["2026-09-25"], TODAY) == 1 and xp.streak_days([], TODAY) == 0

    def test_summary_counts_today_and_the_streak(self):
        answers = [
            xp.ScoredAnswer(day="2026-09-25", band="STRONG", difficulty=1, skills=[("a", 1.0)]),
            xp.ScoredAnswer(day="2026-09-24", band="WEAK", difficulty=1, skills=[("a", 0.5), ("b", 0.5)]),
            xp.ScoredAnswer(day="2026-09-24", band=None, difficulty=1, skills=[("a", 1.0)]),      # unscored: ignored
        ]
        summary = xp.summarise(answers, TODAY)
        assert summary.total == 24 and summary.today == 20 and summary.streak == 2
        assert summary.per_skill == {"a": 22, "b": 2}


class TestLevelProgress:
    def test_fill_inside_the_current_level(self):
        assert xp.level_progress(None, None) == 0.0
        assert xp.level_progress(2, 1.5) == 0.0                     # just reached level 2
        assert xp.level_progress(2, 2.0) == 0.5
        assert xp.level_progress(2, 2.49) == pytest.approx(0.99)
        assert xp.level_progress(5, 4.6) == 1.0                     # the top level is full
        assert xp.level_progress(2, 3.4) == 1.0                     # a capped level shows a full bar


def service(catalog):
    store = InMemoryStore(catalog)
    return PracticeService(store, catalog, scripted([GOOD, GOOD, GOOD]), ServiceConfig(suggest_reviewed_only=False)), store


async def run_flow(svc):
    view = await svc.start(USER, question_key=Q, mode="quick", language="en")
    submission, attempt = await svc.submit(USER, uuid.UUID(view.id), "alarm = AB + BC + AC", idempotency_key="k1")
    progress = await svc.progress(USER, language="en")
    return submission, attempt, progress


class TestOnTheService:
    async def test_xp_appears_after_a_scored_answer(self, catalog):
        svc, store = service(catalog)
        submission, attempt, progress = await run_flow(svc)
        question = catalog.questions[Q]
        assert submission.status == "done" and submission.band is not None
        expected = xp.answer_xp(submission.band, difficulty=question.difficulty)
        assert submission.xp_earned == expected > 0
        assert attempt.submission.xp_earned == expected                    # the reloaded view agrees
        assert progress.overview.xp_total == expected and progress.overview.xp_today == expected
        assert progress.overview.streak_days == 1
        split = xp.split_by_skill(expected, [(link.skill, link.weight) for link in question.skills])
        by_key = {s.key: s for s in progress.skills}
        for key, part in split.items():
            if key in by_key:
                assert by_key[key].xp == part
        primary = by_key[question.primary_skill]
        assert 0.0 <= primary.level_progress <= 1.0
        # the store rows have the shape the database reader returns as well
        async with store.transaction() as tx:
            stored = await tx.scored_submissions(USER)
        assert len(stored) == 1 and stored[0]["band"] == submission.band and stored[0]["turn"] == 0
        assert stored[0]["skills"] and stored[0]["interview"] is False

    async def test_nothing_scored_means_zero_xp_and_no_streak(self, catalog):
        svc, _ = service(catalog)
        progress = await svc.progress(USER, language="en")
        assert progress.overview.xp_total == 0 and progress.overview.xp_today == 0 and progress.overview.streak_days == 0

    async def test_the_engine_is_identical_with_and_without_xp(self, catalog, monkeypatch):
        """Bands, levels and the stored skill states do not change when XP is switched off: XP only reads."""
        svc, store = service(catalog)
        submission, attempt, progress = await run_flow(svc)
        with_xp = (submission.band, attempt.status, [(s.key, s.level, s.status, s.loyalty) for s in progress.skills],
                   progress.overview.level_rank, progress.overview.answered,
                   {k: v["engine_state"] for k, v in store.profiles.items()})

        class Off:
            @staticmethod
            def answer_xp(*a, **k):
                return 0

            @staticmethod
            def summarise(*a, **k):
                return xp.XpSummary()

            from_rows = staticmethod(lambda rows: [])
            level_progress = staticmethod(lambda level, score: 0.0)
            XpSummary = xp.XpSummary

        monkeypatch.setattr(practice_service, "xp", Off)
        svc2, store2 = service(catalog)
        submission2, attempt2, progress2 = await run_flow(svc2)
        without_xp = (submission2.band, attempt2.status, [(s.key, s.level, s.status, s.loyalty) for s in progress2.skills],
                      progress2.overview.level_rank, progress2.overview.answered,
                      {k: v["engine_state"] for k, v in store2.profiles.items()})
        assert with_xp == without_xp
        assert submission2.xp_earned == 0 and progress2.overview.xp_total == 0        # only the layer went dark

    def test_the_xp_module_imports_nothing_from_the_engine(self):
        """A static proof: xp.py depends on the standard library only, so it cannot change an evaluation."""
        tree = ast.parse(Path(xp.__file__).read_text(encoding="utf-8"))
        imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | \
                   {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        assert not any(name and name.startswith("app") for name in imported), imported


class TestTheInterviewTurn:
    async def test_a_revealed_interview_turn_carries_its_xp(self, catalog):
        from tests.test_interview_service import interviewer
        from tests.test_interview_service import service as interview_service
        svc, store = interview_service(catalog, interviewer([GOOD, GOOD, GOOD]))
        view = await svc.start(USER, duration_min=20, language="en")
        turn = view.current_turn
        assert turn is not None and turn.xp_earned is None                     # hidden until the results are revealed
        svc.clock.advance()
        await svc.answer(USER, uuid.UUID(view.id), turn.index, "alarm = AB + BC + AC", idempotency_key="i1")
        ended = await svc.end(USER, uuid.UUID(view.id))
        scored = [t for t in ended.turns if t.band]
        assert scored and all(t.xp_earned == xp.answer_xp(t.band, difficulty=t.difficulty, hints_seen=len(t.hints), interview=True)
                              for t in scored)
        async with store.transaction() as tx:
            rows = await tx.scored_interview_turns(USER)
        assert len(rows) == len(scored) and all(r["interview"] for r in rows)
        assert sum(a.xp for a in xp.from_rows(rows)) == sum(t.xp_earned for t in scored)


# ----------------------------------------------------------------------------- review fixes (2026-09-25)


def test_rounding_is_half_up_like_the_engine():
    from app.engine import xp as xpmod
    # PARTIAL at difficulty 1 with the reference revealed: 10 x 0.25 = 2.5 -> 3 (half up), never 2 (half to even)
    assert xpmod.answer_xp("PARTIAL", difficulty=1, reference_seen=True) == 3


def test_a_follow_up_credits_the_primary_skill_only():
    from datetime import date

    from app.engine import xp as xpmod
    answers = xpmod.from_rows([
        {"day": "2026-09-25", "band": "STRONG", "difficulty": 1, "turn": 1, "skills": [["boolean_algebra", 0.7], ["truth_tables", 0.3]]},
        {"day": "2026-09-25", "band": "STRONG", "difficulty": 1, "turn": 0, "skills": [["boolean_algebra", 0.7], ["truth_tables", 0.3]]},
    ])
    summary = xpmod.summarise(answers, date(2026, 9, 25))
    assert summary.total == 10 + 20
    assert summary.per_skill == {"boolean_algebra": 10 + 14, "truth_tables": 6}


async def test_a_running_interview_earns_no_xp_until_it_is_over():
    import uuid

    from app.engine.catalog import load_catalog
    from app.services.interview_service import InterviewConfig, InterviewService
    from app.services.memory_store import InMemoryStore
    from tests.test_interview_service import Clock, interviewer
    from tests.test_practice_hardening import GOOD, SEEDS

    catalog = load_catalog(SEEDS)
    store = InMemoryStore(catalog)
    svc = InterviewService(store, catalog, interviewer([GOOD]), InterviewConfig(reviewed_only=False))
    svc.clock = Clock()
    user = uuid.uuid4()
    view = await svc.start(user, duration_min=45, language="en")
    await svc.answer(user, uuid.UUID(view.id), view.current_turn.index, "a careful answer", idempotency_key="t0")
    async with store.transaction() as tx:
        assert await tx.scored_interview_turns(user) == []          # results hidden while it runs: XP must not tell
    await svc.end(user, uuid.UUID(view.id))
    async with store.transaction() as tx:
        rows = await tx.scored_interview_turns(user)
    assert rows and all(r["interview"] and len(r["skills"]) == 1 for r in rows)
