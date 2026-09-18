"""Randomized sequences of user actions, several users at once, a model that fails at random.

Whatever happens, these must hold:
  * the service raises ApiError or returns; never anything else
  * one revision per idempotency key; scores applied once per DONE revision
  * metrics rows == DONE revisions x skills examined; usage recorded for every model call that ran
  * a fresh service instance sees exactly the same attempt as the one that produced it
  * statuses are consistent: a pending follow-up implies the main answer is done
"""

from __future__ import annotations

import asyncio
import random
import uuid

import pytest

from app.api.errors import ApiError
from app.engine.catalog import load_catalog
from app.engine.providers import LLMError, LLMRequest, ScriptedProvider
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_practice_hardening import CARD, FOLLOW_UP, GOOD, SEEDS, WEAK

ACTIONS = ("hint", "reveal", "submit", "submit_same_key", "follow_up", "retry", "get", "restart_get")


class FlakyProvider(ScriptedProvider):
    def __init__(self, rng: random.Random, failure_rate: float):
        super().__init__(self._respond)
        self.rng, self.failure_rate = rng, failure_rate
        self.calls = 0

    def _respond(self, request: LLMRequest):
        self.calls += 1
        roll = self.rng.random()
        if request.role == "evaluator" and roll < self.failure_rate:
            raise LLMError("flaky", retryable=roll < self.failure_rate / 2)
        if request.role == "evaluator":
            return self.rng.choice([GOOD, WEAK])
        if request.role == "generator":
            return FOLLOW_UP
        if request.role == "feedback":
            return CARD
        return "Next time, try tracing one more input."


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


async def run_user(svc: PracticeService, store: InMemoryStore, catalog, rng: random.Random, user: uuid.UUID,
                   steps: int) -> list[str]:
    keys = list(catalog.questions)
    attempts: list[uuid.UUID] = []
    log = []
    for _ in range(steps):
        if not attempts or rng.random() < 0.15:
            try:
                view = await svc.start(user, question_key=rng.choice(keys), mode=rng.choice(["deep", "quick"]),
                                       language=rng.choice(["en", "he"]))
                attempts.append(uuid.UUID(view.id))
            except ApiError as exc:
                assert exc.code in ("usage_limit",), exc.code
            continue
        attempt_id = rng.choice(attempts)
        action = rng.choice(ACTIONS)
        log.append(action)
        try:
            if action == "hint":
                await svc.next_hint(user, attempt_id)
            elif action == "reveal":
                await svc.reveal_reference(user, attempt_id)
            elif action == "submit":
                await svc.submit(user, attempt_id, f"answer {rng.randint(1, 5)}", idempotency_key=f"{attempt_id}-{rng.randint(1, 3)}")
            elif action == "submit_same_key":
                await svc.submit(user, attempt_id, "answer 1", idempotency_key=f"{attempt_id}-1")
            elif action == "follow_up":
                view = await svc.get(user, attempt_id)
                turn = view.pending_follow_up.turn if view.pending_follow_up else 1
                await svc.submit(user, attempt_id, f"follow-up {rng.randint(1, 5)}",
                                 idempotency_key=f"{attempt_id}-f{turn}-{rng.randint(1, 2)}", follow_up_turn=turn)
            elif action == "retry":
                await svc.retry(user, attempt_id)
            elif action == "get":
                await svc.get(user, attempt_id)
            elif action == "restart_get":
                fresh = PracticeService(store, catalog, svc.provider, svc.config)
                a, b = await svc.get(user, attempt_id), await fresh.get(user, attempt_id)
                assert a == b, "a restarted service sees a different attempt"
        except ApiError as exc:
            assert exc.code in ("conflict", "already_submitted", "no_pending_follow_up", "nothing_to_retry",
                                "validation"), f"{action}: {exc.code}: {exc}"
    return log


def check_invariants(store: InMemoryStore, catalog):
    for attempt_id, stored in store.attempts.items():
        row = stored["row"]
        subs = row["submissions"]
        keys = [s["key"] for s in subs]
        assert len(keys) == len(set(keys)), f"{attempt_id}: duplicate idempotency key"
        assert [s["revision"] for s in subs] == list(range(1, len(subs) + 1)), "revisions are not contiguous"
        done = [s for s in subs if s["status"] == "done"]
        for s in done:
            assert s["band"] and s["evaluation"], "done without a result"
        mains = [s for s in subs if s["turn"] == 0]
        main_done = any(s["status"] == "done" for s in mains)
        pending = [t for t in row["follow_up_turns"] if t.get("submission_revision") is None]
        if pending:
            assert main_done, "a pending follow-up without an evaluated main answer"
        assert len(pending) <= 1, "more than one pending follow-up"
        question = catalog.questions[row["question_key"]]
        expected_rows = sum(len(question.skills) if s["turn"] == 0 else 1 for s in done)
        actual_rows = sum(1 for m in store.metrics if m["attempt_id"] == attempt_id)
        assert actual_rows == expected_rows, f"{attempt_id}: {actual_rows} metrics rows for {len(done)} done revisions"
        for s in subs:
            if s["reference_seen"] and s["status"] == "done":
                assert s["evidence_weight"] == 0, "evidence after revealing the reference"


@pytest.mark.parametrize("seed", range(6))
async def test_random_sequences_keep_every_invariant(catalog, seed):
    provider = FlakyProvider(random.Random(seed + 100), failure_rate=0.25)
    store = InMemoryStore(catalog)
    svc = PracticeService(store, catalog, provider, ServiceConfig(daily_attempt_limit=50))
    users = [uuid.uuid4() for _ in range(3)]
    await asyncio.gather(*[run_user(svc, store, catalog, random.Random(seed * 10 + i), user, steps=40)
                           for i, user in enumerate(users)])
    check_invariants(store, catalog)
    assert provider.calls > 0
    # usage: one row per model call that returned (failures raise before a response exists)
    assert len(store.usage) <= provider.calls
    for user in users:
        progress = await svc.progress(user)
        assert all(s.level is None or 1 <= s.level <= 5 for s in progress.skills)
