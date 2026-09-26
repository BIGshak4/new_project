"""Grade first, words after: the proof that moving the prose later in time changes no result.

`tests/golden/grade_first_equivalence.json` was written by the code as it was BEFORE the split (2026-09-26, commit
a9d8643), from the scenario below: four attempts (a weak answer with a hint and a follow-up, a Python answer run
against its code tests, a Hebrew answer after the reference was revealed, a strong answer with a follow-up), then the
progress view. Every result is recorded: bands, evaluations, evidence, XP, the next-question suggestion, the card, the
tip, the follow-up wording, the attempt rows, every skill profile's stored engine_state and level history, the
metrics rows, the model-usage rows and the tips delivered. Timestamps and random ids are normalised.

The same scenario then runs on today's code twice, with the prose inline and with the prose in the background, and
both must reproduce the golden record exactly. Regenerate only on purpose: `GOLDEN=write uv run pytest tests/test_grade_first.py`.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import uuid
from datetime import date, datetime
from pathlib import Path

import pytest

from app.engine.providers import LLMRequest, ScriptedProvider
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.conftest import make_evaluation

GOLDEN = Path(__file__).resolve().parent / "golden" / "grade_first_equivalence.json"
SEEDS = Path(__file__).resolve().parent.parent / "seeds"
USER = uuid.UUID("00000000-0000-4000-8000-000000000001")

STRONG = make_evaluation(correctness=0.9, depth=0.8).model_dump()
WEAK = make_evaluation(correctness=0.2, depth=0.2, misconceptions=["xor_confused_with_majority"]).model_dump()
MIDDLE = make_evaluation(correctness=0.55, depth=0.45).model_dump()
COUNT_SET_BITS = "def count_set_bits(x):\n    n = 0\n    while x:\n        x &= x - 1\n        n += 1\n    return n\n"
TIME_KEYS = {"at", "created_at", "accepted_at", "evaluated_at", "evaluating_since", "started_at", "submitted_at",
             "updated_at", "last_assessed_at", "last_assessed", "retention_due_at", "generated_at", "day",
             "runtime_ms", "latency_ms", "eval_latency_ms"}              # wall-clock measurements, not results
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}([T ][\d:.+\-Z]*)?$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def provider() -> ScriptedProvider:
    """Deterministic whatever the call order: every reply depends only on the request."""
    def respond(request: LLMRequest):
        if request.role == "evaluator":
            if "A ^ B ^ C" in request.user:
                return WEAK
            if "maybe" in request.user:
                return MIDDLE
            return STRONG
        if request.role == "generator":
            action = re.search(r'"action":\s*"(\w+)"', request.user)
            return {"question_text": f"Follow-up ({action.group(1) if action else '?'}): what changes if one input is stuck at 1?",
                    "question_archetype": "design", "expected_answer_outline": "the stuck input", "rubric_focus": []}
        if request.role == "feedback":
            band = re.search(r"<band>(\w+)</band>", request.user)
            return {"what_happened": f"band {band.group(1) if band else '?'}", "why_it_matters": "interviews",
                    "next_step": "Next time, trace one more input.", "your_reasoning_vs_reference": "close"}
        return "Polished: " + request.user.split("<tip>")[-1].split("</tip>")[0].strip()[:120]
    return ScriptedProvider(respond)


class Normaliser:
    """Timestamps become <t>, random ids become #1, #2 ... in order of first appearance."""

    def __init__(self):
        self.ids: dict[str, str] = {}

    def __call__(self, value, key: str | None = None):
        if key in TIME_KEYS and value is not None:
            return "<t>"
        if isinstance(value, dict):
            return {str(k): self(v, str(k)) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            items = [self(v) for v in value]
            return sorted(items, key=json.dumps) if isinstance(value, set) else items
        if isinstance(value, (datetime, date)):
            return "<t>"
        if isinstance(value, uuid.UUID):
            value = str(value)
        if isinstance(value, str):
            if UUID_RE.match(value):
                return self.ids.setdefault(value, f"#{len(self.ids) + 1}")
            if ISO.match(value) and len(value) > 10:
                return "<t>"
            return value
        if isinstance(value, float):
            return round(value, 9)
        if hasattr(value, "model_dump"):
            return self(value.model_dump(mode="json"))
        if hasattr(value, "value") and not isinstance(value, (int, bool)):
            return value.value
        return value


GRADE_FIELDS = ("status", "band", "summary", "key_points_hit", "key_points_missed", "check", "evidence", "xp_earned",
                "hints_seen", "reference_seen", "assessed_by", "revision", "turn", "answer", "next_question")


def _config(background: bool | None) -> ServiceConfig:
    kwargs = dict(suggest_reviewed_only=False, polish_tips=True, daily_attempt_limit=100)
    if background is not None and "feedback_in_background" in {f.name for f in dataclasses.fields(ServiceConfig)}:
        kwargs["feedback_in_background"] = background
    return ServiceConfig(**kwargs)


async def _settle(svc: PracticeService) -> None:
    drain = getattr(svc, "drain", None)
    if drain is not None:
        await drain()


async def scenario(catalog, background: bool | None) -> dict:
    store = InMemoryStore(catalog)
    svc = PracticeService(store, catalog, provider(), _config(background))
    norm = Normaliser()
    record: dict = {"answers": [], "attempts": []}
    attempt_ids = []

    async def answer(attempt_id, text, key, *, follow_up=False):
        view = await svc.get(USER, attempt_id)
        turn = None
        if follow_up:
            await _settle(svc)                              # the follow-up question must have its words first
            view = await svc.get(USER, attempt_id)
            if view.pending_follow_up is None:
                record["answers"].append({"key": key, "no_follow_up": True})
                return view
            turn = view.pending_follow_up.turn
        sub, view = await svc.submit(USER, attempt_id, {"text": text}, idempotency_key=key, follow_up_turn=turn)
        record["answers"].append({"key": key, **{f: norm(getattr(sub, f)) for f in GRADE_FIELDS}})
        return view

    async def start(question, language, **kw):
        view = await svc.start(USER, question_key=question, mode="deep", language=language, self_confidence=3)
        attempt_ids.append(uuid.UUID(view.id))
        return uuid.UUID(view.id)

    a1 = await start("example-sensor-majority", "en")
    await svc.next_hint(USER, a1)
    await answer(a1, "alarm = A ^ B ^ C", "a1-main")
    await answer(a1, "maybe an AND of each pair, then an OR", "a1-f1", follow_up=True)

    a2 = await start("example-count-set-bits", "en")
    await answer(a2, COUNT_SET_BITS, "a2-main")
    await answer(a2, "each step clears the lowest set bit, so at most 32 steps", "a2-f1", follow_up=True)

    a3 = await start("example-masked-equality", "he")
    await svc.reveal_reference(USER, a3)
    await answer(a3, "equal = ~|((A ^ B) & M), כלומר NOR על אי־ההתאמות במסכה", "a3-main")

    a4 = await start("example-nand-only-enable", "en")
    await answer(a4, catalog.questions["example-nand-only-enable"].translations["en"].reference_solution, "a4-main")
    await answer(a4, "the stuck input dominates the NAND output", "a4-f1", follow_up=True)
    await _settle(svc)

    for attempt_id in attempt_ids:
        view = await svc.get(USER, attempt_id)
        record["attempts"].append(norm(view.model_dump(mode="json", exclude={"started_at"})))
    progress = await svc.progress(USER, language="en")
    record["progress"] = norm({"overview": progress.overview.model_dump(mode="json"),
                               "skills": [s.model_dump(mode="json") for s in progress.skills],
                               "focus": [s.key for s in progress.focus_skills]})
    record["store"] = norm({
        "attempts": [store.attempts[a]["row"] for a in attempt_ids],
        "profiles": {f"{key}": {"engine_state": row["engine_state"], "version": row["version"],
                                "level_history": row["level_history"], "proficiency_level": row["proficiency_level"],
                                "level_score": row["level_score"], "knowledge_score": row["knowledge_score"],
                                "confidence_score": row["confidence_score"], "trend": row["trend"]}
                     for (_, key), row in sorted(store.profiles.items(), key=lambda kv: kv[0][1])},
        "metrics": store.metrics,
        "usage": store.usage,
        "tips": store.tips,
    })
    # the order in which concurrent model calls finish is not a result: usage rows compared as a sorted multiset
    record["store"]["usage"] = sorted(record["store"]["usage"], key=lambda u: json.dumps(u, sort_keys=True))
    return record


def _strip_new_fields(value, golden):
    """Fields added by the split (feedback_pending, question_pending) must be at rest; everything else must match."""
    if isinstance(value, dict) and isinstance(golden, dict):
        extra = set(value) - set(golden)
        for key in extra:
            assert value[key] in (False, None, [], {}), f"new field {key} not at rest: {value[key]!r}"
        return {k: _strip_new_fields(value[k], golden[k]) for k in golden if k in value} | \
               {k: None for k in golden if k not in value}
    if isinstance(value, list) and isinstance(golden, list) and len(value) == len(golden):
        return [_strip_new_fields(v, g) for v, g in zip(value, golden, strict=True)]
    return value


@pytest.fixture(scope="module")
def catalog():
    from app.engine.catalog import load_catalog
    return load_catalog(SEEDS)


@pytest.mark.parametrize("background", [False, True], ids=["prose-inline", "prose-in-background"])
async def test_the_scenario_reproduces_the_record_written_before_the_split(catalog, background):
    got = await scenario(catalog, background)
    if os.environ.get("GOLDEN") == "write":
        GOLDEN.parent.mkdir(exist_ok=True)
        GOLDEN.write_text(json.dumps(got, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        pytest.skip("golden record written")
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    got = json.loads(json.dumps(got, sort_keys=True, ensure_ascii=False))
    assert _strip_new_fields(got, golden) == golden


# ---------------------------------------------------------------------------------------------- behaviour


def _svc(catalog, prov=None, **config):
    store = InMemoryStore(catalog)
    kwargs = dict(suggest_reviewed_only=False, polish_tips=True, daily_attempt_limit=100, feedback_in_background=True)
    return PracticeService(store, catalog, prov or provider(), ServiceConfig(**{**kwargs, **config})), store


async def _no_sleep(_seconds):
    return None


def _calls(svc: PracticeService, role: str) -> int:
    return sum(1 for r in svc.provider.requests if r.role == role)


def copy_profiles(store: InMemoryStore) -> dict:
    return json.loads(json.dumps({k[1]: {"state": v["engine_state"], "version": v["version"]}
                                  for k, v in store.profiles.items()}, default=str, sort_keys=True))


class TestGradeFirst:
    async def test_the_grade_comes_first_and_the_words_follow(self, catalog):
        import asyncio

        from app.api.errors import ApiError

        gate = asyncio.Event()
        replies = provider()

        async def slow_prose(request):                      # the prose calls wait until the test opens the gate
            if request.role != "evaluator":
                await gate.wait()
            return replies._responder(request)
        svc, store = _svc(catalog, ScriptedProvider(slow_prose))
        view = await svc.start(USER, question_key="example-sensor-majority", mode="deep", language="en")
        aid = uuid.UUID(view.id)
        sub, view = await svc.submit(USER, aid, {"text": "alarm = A ^ B ^ C"}, idempotency_key="k")
        # the grade is complete ...
        assert sub.status == "done" and sub.band == "WEAK" and sub.xp_earned and sub.check is not None and sub.evidence != "none"
        # ... the words are not, and the app is told so
        assert sub.feedback_pending and view.feedback_pending and sub.card is None and sub.tip is None
        assert view.pending_follow_up is not None and view.pending_follow_up.question_pending
        assert view.pending_follow_up.question == ""
        with pytest.raises(ApiError) as refused:            # a follow-up cannot be answered before it has words
            await svc.submit(USER, aid, {"text": "x"}, idempotency_key="f", follow_up_turn=1)
        assert refused.value.code == "follow_up_not_ready"
        metrics_after_grade, profile_after_grade = len(store.metrics), copy_profiles(store)
        gate.set()
        await svc.drain()
        view = await svc.get(USER, aid)
        assert not view.feedback_pending and view.submission.card is not None and view.submission.tip is not None
        assert view.pending_follow_up.question.startswith("Follow-up") and not view.pending_follow_up.question_pending
        assert view.submission.follow_up == view.pending_follow_up.question
        # writing the words scored nothing
        assert len(store.metrics) == metrics_after_grade and copy_profiles(store) == profile_after_grade
        assert len(store.tips) == 1 and {u["action"] for u in store.usage} >= {"generate", "feedback", "tip"}
        sub2, view = await svc.submit(USER, aid, {"text": "maybe an AND of each pair"}, idempotency_key="f",
                                      follow_up_turn=1)
        assert sub2.status == "done" and sub2.band and sub2.feedback_pending        # a follow-up: its tip comes after
        await svc.drain()
        assert not (await svc.get(USER, aid)).feedback_pending

    async def test_words_lost_in_a_crash_are_written_on_the_next_read_and_nothing_is_scored_again(self, catalog,
                                                                                                   monkeypatch):
        from app.services import practice_service

        svc, store = _svc(catalog)
        monkeypatch.setattr(PracticeService, "_start_feedback", lambda *a, **k: None)   # the process dies after the grade
        view = await svc.start(USER, question_key="example-sensor-majority", mode="deep", language="en")
        aid = uuid.UUID(view.id)
        sub, _ = await svc.submit(USER, aid, {"text": "alarm = A ^ B ^ C"}, idempotency_key="k")
        assert sub.feedback_pending
        monkeypatch.undo()
        metrics, profiles, evaluator_calls = len(store.metrics), copy_profiles(store), _calls(svc, "evaluator")

        restarted = PracticeService(store, catalog, svc.provider, svc.config)          # a new process, same database
        view = await restarted.get(USER, aid)                                           # young: another process may be on it
        assert view.feedback_pending and not restarted._feedback_tasks
        monkeypatch.setattr(practice_service, "FEEDBACK_STALE_SECONDS", 0)
        await restarted.get(USER, aid)                                                  # abandoned: resumed
        await restarted.drain()
        view = await restarted.get(USER, aid)
        assert not view.feedback_pending and view.submission.card and view.pending_follow_up.question
        assert len(store.metrics) == metrics and copy_profiles(store) == profiles
        assert _calls(svc, "evaluator") == evaluator_calls                              # never re-scored

    async def test_retry_on_a_wordless_revision_writes_only_the_words_once(self, catalog, monkeypatch):
        svc, store = _svc(catalog)
        monkeypatch.setattr(PracticeService, "_start_feedback", lambda *a, **k: None)
        view = await svc.start(USER, question_key="example-nand-only-enable", mode="deep", language="en")
        aid = uuid.UUID(view.id)
        await svc.submit(USER, aid, {"text": "a NAND answer"}, idempotency_key="k")
        monkeypatch.undo()
        evaluator_calls, metrics = _calls(svc, "evaluator"), len(store.metrics)
        sub, view = await svc.retry(USER, aid)
        assert not sub.feedback_pending and sub.card is not None and not view.feedback_pending
        assert _calls(svc, "evaluator") == evaluator_calls and len(store.metrics) == metrics
        # a second writer (another task, another process) finds the words there and writes nothing
        assert await svc.finish_feedback(USER, aid, sub.revision) is False
        tips_before = len(store.tips)
        assert await svc.finish_feedback(USER, aid, sub.revision) is False
        assert len(store.tips) == tips_before <= 1
        assert (await svc.get(USER, aid)).submission.card == sub.card

    async def test_a_failed_save_of_the_words_is_tried_again(self, catalog, monkeypatch):
        from app.services import practice_service

        svc, store = _svc(catalog)
        real = practice_service.PracticeService._persist_feedback
        failures = {"left": 1}

        async def flaky(self, *args, **kwargs):
            if failures["left"]:
                failures["left"] -= 1
                raise ConnectionError("database connection dropped")
            return await real(self, *args, **kwargs)
        monkeypatch.setattr(practice_service.PracticeService, "_persist_feedback", flaky)
        monkeypatch.setattr(practice_service.asyncio, "sleep", _no_sleep)
        view = await svc.start(USER, question_key="example-sensor-majority", mode="deep", language="en")
        aid = uuid.UUID(view.id)
        await svc.submit(USER, aid, {"text": "alarm = A ^ B ^ C"}, idempotency_key="k")
        await svc.drain()
        view = await svc.get(USER, aid)
        assert not view.feedback_pending and view.submission.card is not None and failures["left"] == 0

    async def test_a_replayed_submit_reports_the_words_as_they_are_and_scores_once(self, catalog):
        svc, store = _svc(catalog)
        view = await svc.start(USER, question_key="example-sensor-majority", mode="deep", language="en")
        aid = uuid.UUID(view.id)
        first, _ = await svc.submit(USER, aid, {"text": "alarm = A ^ B ^ C"}, idempotency_key="k")
        again, _ = await svc.submit(USER, aid, {"text": "alarm = A ^ B ^ C"}, idempotency_key="k")
        assert again.band == first.band and again.replayed
        await svc.drain()
        again, _ = await svc.submit(USER, aid, {"text": "alarm = A ^ B ^ C"}, idempotency_key="k")
        assert not again.feedback_pending and again.card is not None
        assert len(store.metrics) == 2                                      # scored once (two skills examined)

    async def test_a_profile_conflict_undoes_the_wordless_follow_up(self, catalog):
        svc, store = _svc(catalog)
        view = await svc.start(USER, question_key="example-sensor-majority", mode="deep", language="en")
        aid = uuid.UUID(view.id)
        store.failures.add("save_profile")                                  # the profile keeps moving
        sub, view = await svc.submit(USER, aid, {"text": "alarm = A ^ B ^ C"}, idempotency_key="k")
        assert sub.status == "failed" and "profile_conflict" in sub.flags and not sub.feedback_pending
        assert view.pending_follow_up is None and view.follow_ups == [] and not svc._feedback_tasks
        store.failures.discard("save_profile")
        sub, view = await svc.retry(USER, aid)
        assert sub.status == "done" and sub.feedback_pending and view.pending_follow_up.question_pending
        await svc.drain()
        view = await svc.get(USER, aid)
        assert len(view.follow_ups) == 1 and view.pending_follow_up.question
