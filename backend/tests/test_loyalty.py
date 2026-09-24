"""Loyalty: how fresh the evidence behind a skill level is (1..10), and what a stale level does to the plan."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest

from app.engine import plan_router, scores
from app.engine.catalog import load_catalog
from app.engine.plan_router import ProfileSkill
from app.repo.profiles import LoadedProfile, as_profile_skills
from app.schemas.engine import AssessmentMode, EvidenceStatus, Importance, PlanSkill, SkillSource
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_practice_hardening import GOOD, SEEDS, scripted

NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
USER = uuid.uuid4()
Q = "example-sensor-majority"


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


class TestTheArithmetic:
    @pytest.mark.parametrize("days, expected", [(0, 10), (1, 10), (2, 10), (3, 9), (5, 9), (6, 8), (12, 6), (27, 1), (29, 1),
                                                (30, 1), (400, 1)])
    def test_minus_one_every_three_days_never_below_one(self, days, expected):
        assert scores.loyalty(NOW - timedelta(days=days), NOW) == expected

    def test_never_assessed_has_no_loyalty_and_the_future_is_treated_as_today(self):
        assert scores.loyalty(None, NOW) is None
        assert scores.loyalty(NOW + timedelta(days=2), NOW) == 10

    def test_the_provisional_band_starts_at_six(self):
        assert scores.needs_refresh(7) is False and scores.needs_refresh(6) is True and scores.needs_refresh(None) is False
        assert scores.LOYALTY_PROVISIONAL_AT * scores.LOYALTY_DECAY_DAYS == 18      # 12+ days without evidence -> refresh


def _plan_skill(key, required=2):
    return PlanSkill(key=key, subject="digital_fundamentals", source=SkillSource.ROLE, combined_weight=0.2,
                     importance=Importance.CORE, required_level=required, assessment_mode=AssessmentMode.QUESTIONED,
                     planned_turns=1)


class TestThePlanRouter:
    def test_a_stale_level_asks_for_a_refresh_and_a_fresh_one_does_not(self):
        plan = [_plan_skill("counters"), _plan_skill("boolean_algebra")]
        profile = {
            "counters": ProfileSkill("counters", level=3, status=EvidenceStatus.ASSESSED, loyalty=5, days_since_assessed=16),
            "boolean_algebra": ProfileSkill("boolean_algebra", level=3, status=EvidenceStatus.ASSESSED, loyalty=9, days_since_assessed=4),
        }
        acts = plan_router.candidate_activities(plan=plan, profile=profile, today=date(2026, 9, 24),
                                                bank_coverage={"counters": {"quick": 1}, "boolean_algebra": {"quick": 1}})
        stale = [a for a in acts if a.mode == "retention_check"]
        assert [a.skills for a in stale] == [["counters"]] and stale[0].reason_code == "stale"
        text = plan_router.reason_text(stale[0], "en", {"counters": "Counters"})
        assert "16 days" in text and "Counters" in text
        assert "16" in plan_router.reason_text(stale[0], "he", {"counters": "מונים"})
        # a stale refresh is valued like a due retention check
        value = plan_router.activity_value(stale[0], plan=plan, profile=profile, today=date(2026, 9, 24), recent=[],
                                           minutes_available_today=30)
        assert value >= plan_router.DEFAULT_PARAMS.plan_router.w_retention

    def test_a_due_retention_check_wins_over_the_stale_reason(self):
        plan = [_plan_skill("counters")]
        profile = {"counters": ProfileSkill("counters", level=3, status=EvidenceStatus.ASSESSED, loyalty=4,
                                            retention_due_at=date(2026, 9, 20), days_since_assessed=20)}
        acts = plan_router.candidate_activities(plan=plan, profile=profile, today=date(2026, 9, 24), bank_coverage={"counters": {"quick": 1}})
        assert [a.reason_code for a in acts if a.mode == "retention_check"] == ["retention_due"]


class TestOnTheProfile:
    async def test_loyalty_flows_from_the_stored_last_assessed_date(self, catalog):
        store = InMemoryStore(catalog)
        svc = PracticeService(store, catalog, scripted([GOOD]), ServiceConfig(suggest_reviewed_only=False))
        view = await svc.start(USER, question_key=Q, mode="quick", language="en")
        await svc.submit(USER, uuid.UUID(view.id), "alarm = AB + BC + AC", idempotency_key="k1")
        fresh = await svc.progress(USER, language="en")
        primary = next(s for s in fresh.skills if s.key == "boolean_algebra")
        assert primary.loyalty == 10 and primary.needs_refresh is False and fresh.overview.skills_to_refresh == 0

        # twenty days pass without a scored answer on the skill
        for (uid, _key), row in store.profiles.items():
            if uid == USER and row.get("last_assessed_at"):
                row["last_assessed_at"] = row["last_assessed_at"] - timedelta(days=20)
        later = await svc.progress(USER, language="en")
        primary = next(s for s in later.skills if s.key == "boolean_algebra")
        assert primary.loyalty == 4 and primary.needs_refresh is True and primary.level is not None
        assert later.overview.skills_to_refresh >= 1
        assert later.overview.skills_assessed <= fresh.overview.skills_assessed          # a stale level is not counted as assessed
        refresh = [i for i in later.plan.items if i.mode == "retention_check"]
        assert any("boolean_algebra" in [s.key for s in i.skills] for i in refresh)      # both examined skills went stale
        assert min(i.day_index for i in refresh) == 0                                    # before new material

        # a new scored answer brings the loyalty back
        svc2 = PracticeService(store, catalog, scripted([GOOD]), ServiceConfig(suggest_reviewed_only=False))
        view = await svc2.start(USER, question_key=Q, mode="quick", language="en")
        await svc2.submit(USER, uuid.UUID(view.id), "alarm = AB + BC + AC", idempotency_key="k2")
        back = await svc2.progress(USER, language="en")
        assert next(s for s in back.skills if s.key == "boolean_algebra").loyalty == 10

    def test_as_profile_skills_carries_loyalty(self):
        loaded = LoadedProfile(user_id=USER)
        from app.schemas.engine import SkillState
        loaded.states["counters"] = SkillState(key="counters")
        loaded.last_assessed["counters"] = NOW - timedelta(days=9)
        skills = as_profile_skills(loaded, {"counters": 2})
        assert skills["counters"].loyalty is None                                        # no turns: never assessed
