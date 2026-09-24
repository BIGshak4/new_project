"""The user's skill profile: the engine's SkillState per skill, durable.

`engine_state` is the source of truth; the typed columns (proficiency_level, scores,
trend, counts, retention) are derived from it on every write so that Harel's app and
the progress endpoint can read them without knowing the engine.

Writes are optimistic: every row carries `version`; an update says "where version =
the one I loaded". Zero rows updated means another request wrote first, and the
caller must reload and redo its work rather than overwrite it.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app import db
from app.engine import scores
from app.engine.params import DEFAULT_PARAMS, EngineParams
from app.engine.plan_router import ProfileSkill
from app.repo import cache
from app.schemas.engine import EvidenceStatus, SkillState


class StaleProfile(Exception):
    """The profile row changed under us; reload and redo the action."""


@dataclass
class LoadedProfile:
    user_id: uuid.UUID
    states: dict[str, SkillState] = field(default_factory=dict)         # skill key -> state (only skills with a row)
    versions: dict[str, int] = field(default_factory=dict)              # skill key -> version as loaded
    retention: dict[str, dict] = field(default_factory=dict)            # skill key -> {due, passed, last_at}
    level_history: dict[str, list] = field(default_factory=dict)
    last_assessed: dict[str, datetime | None] = field(default_factory=dict)   # skill key -> last scored answer (loyalty)
    seniority: str | None = None                                        # filled by the service on load


async def _skill_ids(connection: AsyncConnection) -> dict[str, uuid.UUID]:
    async def load():
        skill = await db.table("skill")
        return {row.key: row.id for row in await connection.execute(select(skill.c.id, skill.c.key))}
    return await cache.ID_MAPS.get("skill_ids", load)


async def load(connection: AsyncConnection, user_id: uuid.UUID) -> LoadedProfile:
    profile, skill = await db.table("user_skill_profile"), await db.table("skill")
    rows = (await connection.execute(
        select(profile, skill.c.key).join(skill, skill.c.id == profile.c.skill_id).where(profile.c.user_id == user_id))).all()
    loaded = LoadedProfile(user_id=user_id)
    for row in rows:
        state = row.engine_state or {}
        loaded.states[row.key] = SkillState.model_validate({"key": row.key, **state}) if state else SkillState(key=row.key)
        loaded.versions[row.key] = row.version
        loaded.retention[row.key] = {"due": row.retention_due_at, "passed": row.retention_checks_passed,
                                     "last_at": row.last_retention_check_at}
        loaded.level_history[row.key] = list(row.level_history or [])
        loaded.last_assessed[row.key] = row.last_assessed_at
    return loaded


def derived_columns(state: SkillState, previous_history: list, *, attempt_id: uuid.UUID | None, now: datetime,
                    params: EngineParams = DEFAULT_PARAMS) -> dict:
    level, level_score = scores.questioned_level(state, params)
    history = list(previous_history)
    last_level = history[-1]["level"] if history else None
    if level is not None and level != last_level:
        history.append({"attempt_id": str(attempt_id) if attempt_id else None, "level": level, "at": now.isoformat()})
    if state.turns == 0:
        trend = "new"
    elif last_level is None or level is None or level == last_level:
        trend = "stable"
    else:
        trend = "improving" if level > last_level else "declining"
    scored_turns = sum(1 for t in state.history if t.evidence_weight > 0)
    return {
        "proficiency_level": level, "level_score": round(level_score, 2) if level_score is not None else None,
        # k and c are already 0-100 (AI_Engine_Spec §2.5)
        "knowledge_score": round(min(max(state.k, 0.0), 100.0), 2) if state.k is not None else None,
        "confidence_score": round(min(max(state.c, 0.0), 100.0), 2) if state.c is not None else None,
        "assessments_count": min(scored_turns, 32767), "evidence_turns_total": min(state.turns, 2_147_483_647),
        "trend": trend, "level_history": history, "engine_state": state.model_dump(mode="json", exclude={"key"}),
        "updated_at": now,
    }


async def save(connection: AsyncConnection, loaded: LoadedProfile, states: dict[str, SkillState], *,
               attempt_id: uuid.UUID | None = None, params: EngineParams = DEFAULT_PARAMS) -> dict[str, int]:
    """Write every state in `states`; returns the new versions. Raises StaleProfile on a lost race."""
    profile = await db.table("user_skill_profile")
    skill_ids = await _skill_ids(connection)
    now = datetime.now(UTC)
    new_versions = {}
    for key, state in states.items():
        if key not in skill_ids:
            continue                                  # observed / ad-hoc keys have no catalog row
        columns = derived_columns(state, loaded.level_history.get(key, []), attempt_id=attempt_id, now=now, params=params)
        seen = loaded.versions.get(key)
        if seen is None:
            columns.update(first_assessed_at=now if state.turns else None, last_assessed_at=now if state.turns else None)
            result = await connection.execute(
                insert(profile).values(**db.sql_values({"user_id": loaded.user_id, "skill_id": skill_ids[key], "version": 1, **columns}))
                .on_conflict_do_nothing(index_elements=["user_id", "skill_id"]).returning(profile.c.version))
            if result.first() is None:
                raise StaleProfile(key)               # someone inserted this skill meanwhile
            new_versions[key] = 1
        else:
            if state.turns:
                columns["last_assessed_at"] = now
                columns["first_assessed_at"] = func.coalesce(profile.c.first_assessed_at, now)
            result = await connection.execute(
                update(profile).where(profile.c.user_id == loaded.user_id, profile.c.skill_id == skill_ids[key],
                                      profile.c.version == seen)
                .values(**db.sql_values({"version": seen + 1, **columns})).returning(profile.c.version))
            if result.first() is None:
                raise StaleProfile(key)
            new_versions[key] = seen + 1
    return new_versions


async def set_retention(connection: AsyncConnection, user_id: uuid.UUID, key: str, *, due: date | None,
                        passed: int, checked_at: datetime | None = None) -> None:
    profile = await db.table("user_skill_profile")
    skill_ids = await _skill_ids(connection)
    values = {"retention_due_at": due, "retention_checks_passed": passed}
    if checked_at is not None:
        values["last_retention_check_at"] = checked_at
    await connection.execute(update(profile).where(profile.c.user_id == user_id, profile.c.skill_id == skill_ids[key]).values(**db.sql_values(values)))


def as_profile_skills(loaded: LoadedProfile, required_levels: dict[str, int],
                      params: EngineParams = DEFAULT_PARAMS) -> dict[str, ProfileSkill]:
    """What the plan router and the progress endpoint consume."""
    out = {}
    now = datetime.now(UTC)
    for key, state in loaded.states.items():
        level, _ = scores.questioned_level(state, params)
        status = scores.evidence_status(state, required_levels.get(key, 2))
        retention = loaded.retention.get(key, {})
        last = loaded.last_assessed.get(key)
        value = scores.loyalty(last, now) if status != EvidenceStatus.NOT_ASSESSED else None
        out[key] = ProfileSkill(key=key, level=level if status != EvidenceStatus.NOT_ASSESSED else None, status=status,
                                retention_due_at=retention.get("due"), retention_checks_passed=retention.get("passed", 0),
                                loyalty=value, days_since_assessed=int((now - last).total_seconds() // 86400) if last else None)
    return out
