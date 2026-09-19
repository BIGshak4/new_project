"""An in-memory Store with the database's rules, for tests and for running the API
without a database. Same exceptions, same idempotency-key uniqueness, same
optimistic versioning. Questions come from the seed catalog."""

from __future__ import annotations

import copy
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from app.engine.catalog import Catalog
from app.repo.attempts import AlreadyEvaluated, DuplicateSubmissionKey, StoredAttempt
from app.repo.profiles import LoadedProfile, StaleProfile, derived_columns
from app.repo.questions import LoadedQuestion, QuestionSummary, summary
from app.schemas.engine import SkillState


class InMemoryStore:
    def __init__(self, catalog: Catalog, *, allow_in_review: bool = True):
        self.catalog = catalog
        self.allow_in_review = allow_in_review
        self.attempts: dict[uuid.UUID, dict] = {}                 # attempt id -> {user_id, question_id, row, started_at}
        self.profiles: dict[tuple[uuid.UUID, str], dict] = {}     # (user, skill) -> {state, version, history, ...}
        self.metrics: list[dict] = []
        self.usage: list[dict] = []
        self.tips: list[dict] = []
        self.seniority: dict[uuid.UUID, str] = {}
        self.answer_images: dict[str, dict] = {}                 # storage fixture metadata
        self.failures: set[str] = set()                           # names of operations that should raise (tests)
        self.fail_once: set[str] = set()                          # ... only the next time
        self._commits = 0

    @asynccontextmanager
    async def transaction(self):
        # a snapshot, restored if the unit of work raises: the transactional promise in miniature.
        # If another transaction committed meanwhile (an interleaved "server"), its work stays,
        # as it would in a real database; only a clean, uninterleaved failure is rolled back.
        # shallow copies suffice: saved rows are deep-copied on the way in and never mutated in place,
        # so rolling back means restoring the containers, not the rows (a full deepcopy per action
        # made every action slower as the store grew)
        snapshot = (dict(self.attempts), dict(self.profiles), list(self.metrics), list(self.usage), list(self.tips))
        commits_before = self._commits
        try:
            yield _MemoryTx(self)
        except BaseException:
            if self._commits == commits_before:
                self.attempts, self.profiles, self.metrics, self.usage, self.tips = snapshot
            raise
        self._commits += 1

    @staticmethod
    def question_id(key: str) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_URL, f"question:{key}")


class _MemoryTx:
    def __init__(self, store: InMemoryStore):
        self.s = store

    async def validate_answer_images(self, user_id, attempt_id, images):
        return all(i.path.startswith(f"{user_id}/{attempt_id}/") and
                   self.s.answer_images.get(i.path) == {"mime": i.mime, "size": i.size} for i in images)

    def _servable(self, q) -> bool:
        return q.status == "published" or (self.s.allow_in_review and q.status == "in_review")

    async def load_question(self, *, key=None, question_id=None):
        if key is None:
            key = next((k for k in self.s.catalog.questions if self.s.question_id(k) == question_id), None)
        q = self.s.catalog.questions.get(key) if key else None
        if q is None or not self._servable(q):
            return None
        return LoadedQuestion(id=self.s.question_id(q.key), question=q, version=q.version)

    async def list_questions(self, *, language, subject=None) -> list[QuestionSummary]:
        out = []
        for q in sorted(self.s.catalog.questions.values(), key=lambda q: (q.difficulty, q.key)):
            if self._servable(q) and (subject is None or q.subject == subject):
                out.append(summary(LoadedQuestion(id=self.s.question_id(q.key), question=q, version=q.version), language))
        return out

    async def load_attempt(self, attempt_id, *, user_id):
        stored = self.s.attempts.get(attempt_id)
        if stored is None or stored["user_id"] != user_id:
            return None
        return StoredAttempt(id=attempt_id, user_id=user_id, question_id=stored["question_id"],
                             question_key=stored["row"]["question_key"], started_at=stored["started_at"],
                             row=copy.deepcopy(stored["row"]))

    async def save_attempt(self, *, user_id, question_id, row, revisions=None, known_revisions=0):
        if "save_attempt" in self.s.failures:
            raise RuntimeError("simulated database failure")
        attempt_id = uuid.UUID(str(row["id"]))
        existing = self.s.attempts.get(attempt_id)
        if existing is not None:
            by_revision = {s["revision"]: s for s in existing["row"]["submissions"]}
            keys = {s["key"] for s in by_revision.values()}
            for s in row["submissions"]:
                if revisions is not None and s["revision"] not in revisions:
                    continue
                current = by_revision.get(s["revision"])
                if s["revision"] > known_revisions:
                    if current is not None or s["key"] in keys:
                        raise DuplicateSubmissionKey(s["key"])          # revision number or key taken meanwhile
                elif current is not None and current["status"] == "done" and s["status"] != current["status"]:
                    raise AlreadyEvaluated(s["revision"])
        self.s.attempts[attempt_id] = {"user_id": user_id, "question_id": question_id, "row": copy.deepcopy(row),
                                       "started_at": existing["started_at"] if existing else datetime.now(UTC)}

    async def started_today(self, user_id, *, now=None):
        now = now or datetime.now(UTC)
        day_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
        return sum(1 for a in self.s.attempts.values() if a["user_id"] == user_id and a["started_at"] >= day_start)

    async def recent_attempts(self, user_id, *, limit=20):
        mine = sorted((a for a in self.s.attempts.values() if a["user_id"] == user_id),
                      key=lambda a: a["started_at"], reverse=True)[:limit]
        return [{"id": a["row"]["id"], "question_key": a["row"]["question_key"], "mode": a["row"]["mode"],
                 "band": a["row"]["band"], "started_at": a["started_at"].isoformat(),
                 "submitted_at": None, "language": a["row"]["practice_language"], "hints_used": a["row"]["hints_used"],
                 "reference_revealed": a["row"]["reference_revealed"]} for a in mine]

    async def load_profile(self, user_id):
        loaded = LoadedProfile(user_id=user_id)
        for (uid, key), row in self.s.profiles.items():
            if uid != user_id:
                continue
            loaded.states[key] = SkillState.model_validate({"key": key, **row["engine_state"]})
            loaded.versions[key] = row["version"]
            loaded.retention[key] = {"due": row.get("retention_due_at"), "passed": row.get("retention_checks_passed", 0),
                                     "last_at": None}
            loaded.level_history[key] = list(row["level_history"])
        return loaded

    async def save_profile(self, loaded, states, *, attempt_id=None):
        if "save_profile" in self.s.failures or "save_profile" in self.s.fail_once:
            self.s.fail_once.discard("save_profile")
            raise StaleProfile("simulated")
        now = datetime.now(UTC)
        versions = {}
        for key, state in states.items():
            if key not in self.s.catalog.skills:
                continue
            columns = derived_columns(state, loaded.level_history.get(key, []), attempt_id=attempt_id, now=now)
            current = self.s.profiles.get((loaded.user_id, key))
            seen = loaded.versions.get(key)
            if seen is None:
                if current is not None:
                    raise StaleProfile(key)
                version = 1
            else:
                if current is None or current["version"] != seen:
                    raise StaleProfile(key)
                version = seen + 1
            self.s.profiles[(loaded.user_id, key)] = {**columns, "version": version,
                                                      "last_assessed_at": now if state.turns else None}
            versions[key] = version
        return versions

    async def user_seniority(self, user_id):
        return self.s.seniority.get(user_id)

    async def record_metrics(self, *, user_id, attempt_id, metrics, seniority):
        self.s.metrics.extend({**m, "user_id": user_id, "attempt_id": attempt_id} for m in metrics)
        return len(metrics)

    async def record_usage(self, *, user_id, attempt_id, usage_rows):
        self.s.usage.extend({**u, "user_id": user_id, "attempt_id": attempt_id} for u in usage_rows)
        return len(usage_rows)

    async def record_tip(self, *, attempt_id, tip_key, skill_key, text):
        self.s.tips.append({"attempt_id": attempt_id, "tip_key": tip_key, "skill_key": skill_key, "text": text})
