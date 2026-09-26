"""An in-memory Store with the database's rules, for tests and for running the API
without a database. Same exceptions, same idempotency-key uniqueness, same
optimistic versioning. Questions come from the seed catalog."""

from __future__ import annotations

import copy
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from app.engine.catalog import Catalog
from app.repo.attempts import AlreadyEvaluated, DuplicateSubmissionKey, StoredAttempt
from app.repo.plans import PlanItemRow, StoredPlan
from app.repo.profiles import LoadedProfile, StaleProfile, derived_columns
from app.repo.questions import LoadedQuestion, QuestionSummary, summary
from app.repo.sessions import StaleSession, StoredSession
from app.repo.sightings import SightingsUnavailable, clean_name, slugify
from app.repo.users import Goal
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
        self.sessions: dict[uuid.UUID, dict] = {}                 # interview id -> {user_id, row, turns, plan, created_at}
        self.seniority: dict[uuid.UUID, str] = {}
        self.goals: dict[uuid.UUID, Goal] = {}
        self.plans: dict[uuid.UUID, StoredPlan] = {}                # user id -> the active plan
        self.plan_links: dict[uuid.UUID, uuid.UUID] = {}            # attempt id -> plan item id
        self.sightings: list[dict] = []                            # {question_id, user_id, company_name, company_slug}
        self.sightings_enabled = True                              # False imitates a database without the table
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
        snapshot = (dict(self.attempts), dict(self.profiles), list(self.metrics), list(self.usage), list(self.tips),
                    dict(self.sessions), dict(self.goals), list(self.sightings), copy.deepcopy(self.plans), dict(self.plan_links))
        commits_before = self._commits
        try:
            yield _MemoryTx(self)
        except BaseException:
            if self._commits == commits_before:
                (self.attempts, self.profiles, self.metrics, self.usage, self.tips, self.sessions, self.goals,
                 self.sightings, self.plans, self.plan_links) = snapshot
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
        return q.status in ("published", "trial") or (self.s.allow_in_review and q.status == "in_review")

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

    # ------------------------------------------------------------------ company sightings and the goal

    async def sightings_for(self, question_ids):
        wanted = {str(i) for i in question_ids}
        counts: dict[str, dict[str, dict]] = {}
        for row in self.s.sightings:
            if row["question_id"] in wanted:
                tag = counts.setdefault(row["question_id"], {}).setdefault(
                    row["company_slug"], {"slug": row["company_slug"], "name": row["company_name"], "count": 0})
                tag["count"] += 1
        return {qid: sorted(tags.values(), key=lambda t: (-t["count"], t["slug"])) for qid, tags in counts.items()}

    async def add_sighting(self, *, question_id, user_id, company):
        if not self.s.sightings_enabled:
            raise SightingsUnavailable("company tags are not enabled on this database yet")
        name, slug = clean_name(company), slugify(company)
        if not name or not slug:
            raise ValueError("a company name is required")
        row = {"question_id": str(question_id), "user_id": user_id, "company_name": name, "company_slug": slug}
        if not any(r["question_id"] == row["question_id"] and r["user_id"] == user_id and r["company_slug"] == slug
                   for r in self.s.sightings):
            self.s.sightings.append(row)
        return slug

    async def question_ids_for_company(self, slug):
        return {r["question_id"] for r in self.s.sightings if r["company_slug"] == slug}

    async def companies(self):
        out: dict[str, dict] = {}
        for r in self.s.sightings:
            entry = out.setdefault(r["company_slug"], {"slug": r["company_slug"], "name": r["company_name"],
                                                       "questions": set(), "sightings": 0})
            entry["questions"].add(r["question_id"])
            entry["sightings"] += 1
        rows = [{**e, "questions": len(e["questions"])} for e in out.values()]
        return sorted(rows, key=lambda c: (-c["questions"], c["slug"]))

    async def load_goal(self, user_id):
        goal = self.s.goals.get(user_id)
        if goal is None:
            return Goal(seniority=self.s.seniority.get(user_id))
        return Goal(**goal.__dict__)

    async def save_goal(self, user_id, goal):
        kept = goal.seniority or self.s.seniority.get(user_id)          # None keeps the stored seniority, as the database does
        self.s.goals[user_id] = Goal(**{**goal.__dict__, "seniority": kept})
        if goal.seniority:
            self.s.seniority[user_id] = goal.seniority
        return self.s.goals[user_id]

    async def daily_bands(self, user_id):
        out: dict[str, dict] = {}
        for a in sorted(self.s.attempts.values(), key=lambda a: a["started_at"]):
            if a["user_id"] == user_id and a["row"]["band"]:
                key = a["started_at"].date().isoformat()
                entry = out.setdefault(key, {"day": key, "STRONG": 0, "PARTIAL": 0, "WEAK": 0})
                entry[a["row"]["band"]] = entry.get(a["row"]["band"], 0) + 1
        return [out[k] for k in sorted(out)]

    # ------------------------------------------------------------------ XP reads (same shape as the database readers)

    def _links(self, question_key: str) -> list[list]:
        """The question's skill links, the primary skill first (as the database reader orders them)."""
        question = self.s.catalog.questions.get(question_key)
        if question is None:
            return []
        links = sorted(question.skills, key=lambda link: (not link.primary, -link.weight))
        return [[link.skill, float(link.weight)] for link in links]

    async def scored_submissions(self, user_id, *, days=None):
        since = datetime.now(UTC) - timedelta(days=days) if days is not None else datetime.min.replace(tzinfo=UTC)
        out = []
        for a in sorted(self.s.attempts.values(), key=lambda a: a["started_at"]):
            if a["user_id"] != user_id:
                continue
            question = self.s.catalog.questions.get(a["row"]["question_key"])
            for s in a["row"]["submissions"]:
                if s.get("status") != "done" or not s.get("band"):
                    continue
                accepted = datetime.fromisoformat(s["accepted_at"])
                if accepted.tzinfo is None:
                    accepted = accepted.replace(tzinfo=UTC)
                if accepted < since:
                    continue
                out.append({"day": accepted.astimezone(UTC).date().isoformat(), "band": str(s["band"]),
                            "difficulty": int(question.difficulty if question else 1), "hints_seen": int(s.get("hints_seen") or 0),
                            "reference_seen": bool(s.get("reference_seen")), "turn": int(s.get("turn") or 0), "interview": False,
                            "skills": self._links(a["row"]["question_key"])})
        return out

    async def scored_interview_turns(self, user_id, *, days=None):
        since = datetime.now(UTC) - timedelta(days=days) if days is not None else datetime.min.replace(tzinfo=UTC)
        out = []
        for s in sorted(self.s.sessions.values(), key=lambda s: s["created_at"]):
            if s["user_id"] != user_id or s["created_at"] < since or s["row"].get("status") != "completed":
                continue                                  # a running interview's results are hidden: no XP yet
            for t in s["turns"]:
                meta = t.get("question_generation_meta") or {}
                if meta.get("status") != "done" or not meta.get("band"):
                    continue
                when = t.get("answer_submitted_at") or t.get("created_at")
                stamp = datetime.fromisoformat(when) if isinstance(when, str) else (when or s["created_at"])
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=UTC)
                out.append({"day": stamp.astimezone(UTC).date().isoformat(), "band": str(meta["band"]),
                            "difficulty": int(t.get("difficulty") or 1), "hints_seen": int(meta.get("hint_level") or 0),
                            "reference_seen": False, "turn": 0, "interview": True,
                            "skills": [[t["skill_key"], 1.0]]})
        return out

    # ------------------------------------------------------------------ the saved program

    async def load_active_plan(self, user_id):
        plan = self.s.plans.get(user_id)
        return copy.deepcopy(plan) if plan is not None else None

    async def create_plan(self, *, user_id, role_slug, seniority, week_start, minutes_per_day, interview_date, items):
        now = datetime.now(UTC)
        rows = [PlanItemRow(id=uuid.uuid4(), day_index=int(i["day_index"]), mode=i["mode"], skills=list(i["skills"]),
                            reason=i["reason"] or "-", minutes=max(1, min(120, int(i["minutes"] or 1))),
                            created_at=i.get("created_at") or now) for i in items]
        plan = StoredPlan(id=uuid.uuid4(), user_id=user_id, week_start=week_start, minutes_per_day=minutes_per_day,
                          interview_date=interview_date, seniority=seniority, generated_at=now, items=rows)
        self.s.plans[user_id] = plan
        return copy.deepcopy(plan)

    async def deactivate_plan(self, user_id):
        self.s.plans.pop(user_id, None)

    async def update_plan_item(self, item_id, **fields):
        for plan in self.s.plans.values():
            for item in plan.items:
                if item.id == item_id:
                    for name, value in fields.items():
                        setattr(item, name, value)

    async def link_attempt_to_plan_item(self, attempt_id, item_id):
        self.s.plan_links[attempt_id] = item_id

    async def attempt_plan_item(self, attempt_id):
        return self.s.plan_links.get(attempt_id)

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

    async def save_prose(self, *, user_id, question_id, row, revision):
        if "save_attempt" in self.s.failures:
            raise RuntimeError("simulated database failure")
        existing = self.s.attempts.get(uuid.UUID(str(row["id"])))
        current = next((s for s in (existing or {}).get("row", {}).get("submissions", []) if s["revision"] == revision), None)
        if current is None or current["status"] != "done" or "feedback_pending" not in (current.get("flags") or []):
            return False                                  # the words are already there: never written twice
        self.s.attempts[uuid.UUID(str(row["id"]))] = {**existing, "row": copy.deepcopy(row)}
        return True

    async def started_today(self, user_id, *, now=None):
        now = now or datetime.now(UTC)
        day_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
        return sum(1 for a in self.s.attempts.values() if a["user_id"] == user_id and a["started_at"] >= day_start)

    async def recent_attempts(self, user_id, *, limit=20):
        mine = sorted((a for a in self.s.attempts.values() if a["user_id"] == user_id),
                      key=lambda a: a["started_at"], reverse=True)[:limit]
        return [{"id": a["row"]["id"], "question_key": a["row"]["question_key"],
                 "subject": self.s.catalog.questions[a["row"]["question_key"]].subject, "mode": a["row"]["mode"],
                 "band": a["row"]["band"], "started_at": a["started_at"].isoformat(),
                 "submitted_at": None, "language": a["row"]["practice_language"], "hints_used": a["row"]["hints_used"],
                 "reference_revealed": a["row"]["reference_revealed"]} for a in mine]

    async def band_counts(self, user_id):
        out: dict[str, dict[str, int]] = {}
        for a in self.s.attempts.values():
            if a["user_id"] == user_id and a["row"]["band"]:
                subject = self.s.catalog.questions[a["row"]["question_key"]].subject
                out.setdefault(subject, {})[a["row"]["band"]] = out.get(subject, {}).get(a["row"]["band"], 0) + 1
        return out

    async def seen_question_keys(self, user_id, *, days=30):
        since = datetime.now(UTC) - timedelta(days=days)                 # same window as the database version
        return {a["row"]["question_key"] for a in self.s.attempts.values()
                if a["user_id"] == user_id and a["started_at"] >= since}

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
            loaded.last_assessed[key] = row.get("last_assessed_at")
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

    # ------------------------------------------------------------------ mock interviews

    async def load_session(self, session_id, *, user_id):
        stored = self.s.sessions.get(session_id)
        if stored is None or stored["user_id"] != user_id:
            return None
        return StoredSession(id=session_id, user_id=user_id, row=copy.deepcopy(stored["row"]),
                             turns=copy.deepcopy(stored["turns"]))

    async def save_session(self, *, user_id, row, turns, plan, role_slug, company_slug, expected_revision=None):
        if "save_session" in self.s.failures or "save_session" in self.s.fail_once:
            self.s.fail_once.discard("save_session")
            raise ConnectionError("simulated database failure")
        session_id = uuid.UUID(row["id"])
        current = self.s.sessions.get(session_id)
        if expected_revision is not None:
            stored_revision = int((current or {}).get("row", {}).get("state", {}).get("revision", 0)) if current else None
            if current is None or stored_revision != expected_revision:
                raise StaleSession(f"interview {session_id} moved past revision {expected_revision}")
        by_index = {t["turn_index"]: copy.deepcopy(t) for t in (current["turns"] if current else [])}
        for t in turns:
            by_index[t["turn_index"]] = copy.deepcopy(t)
        self.s.sessions[session_id] = {
            "user_id": user_id, "row": copy.deepcopy(row), "turns": [by_index[i] for i in sorted(by_index)],
            "plan": copy.deepcopy(plan) if plan is not None else (current["plan"] if current else None),
            "created_at": current["created_at"] if current else datetime.now(UTC)}

    async def list_sessions(self, user_id, *, limit=20):
        mine = sorted((s for s in self.s.sessions.values() if s["user_id"] == user_id),
                      key=lambda s: s["created_at"], reverse=True)[:limit]
        return [{"id": s["row"]["id"], "status": s["row"]["status"], "duration_min": s["row"]["config"].get("duration_min"),
                 "language": s["row"]["config"].get("language"), "turn_count": s["row"]["turn_count"],
                 "started_at": s["row"].get("started_at"), "ended_at": s["row"].get("ended_at")} for s in mine]

    async def sessions_started_today(self, user_id):
        today = datetime.now(UTC).date()
        return sum(1 for s in self.s.sessions.values() if s["user_id"] == user_id and s["created_at"].date() == today)

    async def record_session_metrics(self, *, user_id, session_id, metrics, seniority, role_slug, company_slug):
        self.s.metrics.extend({**m, "user_id": user_id, "session_id": session_id} for m in metrics)
        return len(metrics)

    async def record_session_usage(self, *, user_id, session_id, usage_rows):
        self.s.usage.extend({**u, "user_id": user_id, "session_id": session_id} for u in usage_rows)
        return len(usage_rows)
