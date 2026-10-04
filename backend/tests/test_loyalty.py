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
    @pytest.mark.parametrize("days, expected", [(0, 10), (1, 10), (6, 10), (7, 9), (13, 9), (14, 8), (20, 8), (21, 7),
                                                (48, 4), (49, 3), (62, 2), (63, 1), (400, 1)])
    def test_minus_one_every_seven_days_never_below_one(self, days, expected):
        """Shaked, 2026-10-04: one point every 7 days (was 3)."""
        assert scores.loyalty(NOW - timedelta(days=days), NOW) == expected

    def test_never_assessed_has_no_loyalty_and_the_future_is_treated_as_today(self):
        assert scores.loyalty(None, NOW) is None
        assert scores.loyalty(NOW + timedelta(days=2), NOW) == 10

    def test_a_refresh_from_three_weeks_and_expiry_from_seven(self):
        assert scores.needs_refresh(8) is False and scores.needs_refresh(7) is True and scores.needs_refresh(None) is False
        assert scores.expired(4) is False and scores.expired(3) is True and scores.expired(None) is False
        three_weeks, seven_weeks = NOW - timedelta(days=21), NOW - timedelta(days=49)
        assert scores.needs_refresh(scores.loyalty(three_weeks, NOW)) and not scores.expired(scores.loyalty(three_weeks, NOW))
        assert scores.expired(scores.loyalty(seven_weeks, NOW))
        assert not scores.expired(scores.loyalty(NOW - timedelta(days=48), NOW))


def _plan_skill(key, required=2):
    return PlanSkill(key=key, subject="digital_fundamentals", source=SkillSource.ROLE, combined_weight=0.2,
                     importance=Importance.CORE, required_level=required, assessment_mode=AssessmentMode.QUESTIONED,
                     planned_turns=1)


class TestThePlanRouter:
    def test_a_stale_level_asks_for_a_refresh_and_a_fresh_one_does_not(self):
        plan = [_plan_skill("counters"), _plan_skill("boolean_algebra")]
        profile = {
            "counters": ProfileSkill("counters", level=3, status=EvidenceStatus.ASSESSED, loyalty=6, days_since_assessed=28),
            "boolean_algebra": ProfileSkill("boolean_algebra", level=3, status=EvidenceStatus.ASSESSED, loyalty=9, days_since_assessed=4),
        }
        acts = plan_router.candidate_activities(plan=plan, profile=profile, today=date(2026, 9, 24),
                                                bank_coverage={"counters": {"quick": 1}, "boolean_algebra": {"quick": 1}})
        stale = [a for a in acts if a.mode == "retention_check"]
        assert [a.skills for a in stale] == [["counters"]] and stale[0].reason_code == "stale"
        text = plan_router.reason_text(stale[0], "en", {"counters": "Counters"})
        assert "28 days" in text and "Counters" in text
        assert "28" in plan_router.reason_text(stale[0], "he", {"counters": "מונים"})
        # a stale refresh is valued like a due retention check
        value = plan_router.activity_value(stale[0], plan=plan, profile=profile, today=date(2026, 9, 24), recent=[],
                                           minutes_available_today=30)
        assert value >= plan_router.DEFAULT_PARAMS.plan_router.w_retention

    def test_an_expired_level_is_planned_like_a_skill_never_seen(self):
        """49+ days: no retention check, a plain question with the 'expired' reason, valued as unassessed and heavy."""
        plan = [_plan_skill("counters"), _plan_skill("boolean_algebra")]
        profile = {"counters": ProfileSkill("counters", level=3, status=EvidenceStatus.ASSESSED, loyalty=3, days_since_assessed=50)}
        acts = plan_router.candidate_activities(plan=plan, profile=profile, today=date(2026, 9, 24),
                                                bank_coverage={"counters": {"quick": 1}, "boolean_algebra": {"quick": 1}})
        assert not [a for a in acts if a.mode == "retention_check"]
        expired = next(a for a in acts if a.skills == ["counters"])
        assert expired.reason_code == "expired" and profile["counters"].expired
        assert "50 days" in plan_router.reason_text(expired, "en", {"counters": "Counters"})
        unseen = next(a for a in acts if a.skills == ["boolean_algebra"])
        value = lambda a: plan_router.activity_value(a, plan=plan, profile=profile, today=date(2026, 9, 24), recent=[], minutes_available_today=30)  # noqa: E731
        assert value(expired) == value(unseen)                                       # worth exactly as much as never seen

    def test_the_heaviest_unseen_skill_beats_the_variety_bonus(self):
        """The gap and never-seen terms are scaled to the heaviest skill's weight (Shaked, 2026-10-04), so a heavy
        skill with no evidence outranks a light one that only wins on variety of mode."""
        heavy, light = _plan_skill("fsm_state_tables"), _plan_skill("reset_strategies")
        heavy = heavy.model_copy(update={"combined_weight": 0.2})
        light = light.model_copy(update={"combined_weight": 0.05})
        plan = [heavy, light]
        recent = [plan_router.RecentActivity("quick"), plan_router.RecentActivity("quick")]      # variety favours deep now
        heavy_quick = plan_router.Activity("quick", ["fsm_state_tables"], 4, reason_code="unassessed")
        light_deep = plan_router.Activity("deep", ["reset_strategies"], 20, reason_code="unassessed")
        value = lambda a: plan_router.activity_value(a, plan=plan, profile={}, today=date(2026, 10, 5), recent=recent, minutes_available_today=30)  # noqa: E731
        assert value(heavy_quick) > value(light_deep)

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

        # three weeks pass without a scored answer on the skill
        for (uid, _key), row in store.profiles.items():
            if uid == USER and row.get("last_assessed_at"):
                row["last_assessed_at"] = row["last_assessed_at"] - timedelta(days=21)
        store.plans.clear()                                   # the program is rebuilt each new day; imitate the next morning
        later = await svc.progress(USER, language="en")
        primary = next(s for s in later.skills if s.key == "boolean_algebra")
        assert primary.loyalty == 7 and primary.needs_refresh is True and primary.level is not None and not primary.expired
        assert later.overview.skills_to_refresh >= 1
        assert later.overview.skills_assessed <= fresh.overview.skills_assessed          # a stale level is not counted as assessed
        refresh = [i for i in later.plan.items if i.mode == "retention_check"]
        assert any("boolean_algebra" in [s.key for s in i.skills] for i in refresh)      # both examined skills went stale
        assert min(i.day_index for i in refresh) <= 1          # early: the heaviest unseen skills may come first (2026-10-04)

        # seven weeks: the evidence has expired; the level is history, the skill counts as unassessed, and the plan asks
        # it again as a plain question, not a retention check
        for (uid, _key), row in store.profiles.items():
            if uid == USER and row.get("last_assessed_at"):
                row["last_assessed_at"] = row["last_assessed_at"] - timedelta(days=28)
        store.plans.clear()
        gone = await svc.progress(USER, language="en")
        primary = next(s for s in gone.skills if s.key == "boolean_algebra")
        assert primary.loyalty == 3 and primary.expired and primary.status == "insufficient_evidence" and primary.level is not None
        assert gone.overview.skills_assessed == 0
        asked = [i for i in gone.plan.items if "boolean_algebra" in [s.key for s in i.skills] and i.mode in ("quick", "deep")]
        assert asked and not [i for i in gone.plan.items if i.mode == "retention_check"
                              and "boolean_algebra" in [s.key for s in i.skills]]

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
