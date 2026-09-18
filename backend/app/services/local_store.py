"""A JSON file that stands in for the database while practicing from the terminal.

It keeps the same things the database keeps per user: the running state of every
skill, which questions were seen, and the attempts with their metrics rows. That is
enough for "the next question suits me" to work before the API layer exists.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

from app.engine import scores
from app.engine.plan_router import ProfileSkill, RecentActivity
from app.schemas.engine import EvidenceStatus, SkillState


class LocalStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = {"skills": {}, "seen_questions": [], "attempts": [], "recent": [], "retention": {},
                     "usage": [], "created_at": datetime.now(UTC).isoformat()}
        if self.path.exists():
            self.data.update(json.loads(self.path.read_text(encoding="utf-8")))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=1), encoding="utf-8")

    # ------------------------------------------------------------------ skills

    def skill_states(self) -> dict[str, SkillState]:
        return {key: SkillState.model_validate(value) for key, value in self.data["skills"].items()}

    def put_skill_states(self, states: dict[str, SkillState]) -> None:
        for key, state in states.items():
            self.data["skills"][key] = state.model_dump(mode="json")

    def profile(self, required_levels: dict[str, int]) -> dict[str, ProfileSkill]:
        profile = {}
        for key, state in self.skill_states().items():
            level, _ = scores.questioned_level(state)
            status = scores.evidence_status(state, required_levels.get(key, 2))
            retention = self.data["retention"].get(key, {})
            due = retention.get("due")
            profile[key] = ProfileSkill(
                key=key, level=level if status != EvidenceStatus.NOT_ASSESSED else None, status=status,
                retention_due_at=date.fromisoformat(due) if due else None,
                retention_checks_passed=retention.get("passed", 0))
        return profile

    def set_retention(self, key: str, due: date | None, passed: int) -> None:
        self.data["retention"][key] = {"due": due.isoformat() if due else None, "passed": passed}

    # ------------------------------------------------------------------ history

    @property
    def seen_questions(self) -> set[str]:
        return set(self.data["seen_questions"])

    def recent_activities(self) -> list[RecentActivity]:
        return [RecentActivity(**item) for item in self.data["recent"][-7:]]

    def record_attempt(self, attempt_row: dict, metrics: list[dict], usage: list[dict], band: str | None) -> None:
        now = datetime.now(UTC).isoformat()
        key = attempt_row["question_key"]
        if key not in self.data["seen_questions"]:
            self.data["seen_questions"].append(key)
        self.data["attempts"].append({**attempt_row, "metrics": metrics, "submitted_at": now})
        self.data["recent"].append({"mode": attempt_row["mode"], "band": band})
        self.data["usage"].extend({**row, "created_at": now} for row in usage)

    def total_cost_usd(self) -> float:
        return round(sum(row.get("cost_usd", 0.0) for row in self.data["usage"]), 4)
