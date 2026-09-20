"""The new practice flow end to end on the REAL model, without database writes.

    main answer -> evaluation -> (one) follow-up -> evaluation -> suggested next question with its focus

Three attempts: a wrong majority answer (XOR mistake) in English, a buggy Python answer in Hebrew
(the code test runs and fails), and a drawn majority circuit (the derived function passes the check).
Uses the in-memory store, so nothing is persisted. Costs about half a dollar. Needs ANTHROPIC_API_KEY.

    uv run python scripts/e2e_real_flow.py
"""

from __future__ import annotations

import asyncio
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.engine.catalog import load_catalog  # noqa: E402
from app.engine.providers import build_provider  # noqa: E402
from app.services.memory_store import InMemoryStore  # noqa: E402
from app.services.practice_service import PracticeService, ServiceConfig  # noqa: E402

XOR_ANSWER = ("alarm = A ^ B ^ C. XOR of the three sensors gives 1 whenever more than one input is 1, which is exactly "
              "the majority condition, so no further simplification is needed.")
FOLLOW_UP_ANSWER = ("Majority means at least two of the three inputs are 1: alarm = AB + BC + AC. XOR would give 0 for two "
                    "inputs high and 1 for three, so it is odd parity, not majority.")
HEBREW_CODE = ("סופרים ביטים בלולאה על כל ביט. הסיבוכיות O(32) כלומר O(1) לרוחב קבוע, ומקום O(1).\n\n"
               "```python\ndef count_set_bits(x):\n    total = 0\n    for i in range(31):\n        total += (x >> i) & 1\n    return total\n```")


def part(id, kind, label, **over):
    return {"id": id, "kind": kind, "label": label, "x": 0, "y": 0, "count": over.pop("count", 2), "bits": 1, "value": 0, **over}


def wire(src, sp, dst, dp):
    return {"id": f"{src}{sp}-{dst}{dp}", "source": src, "sourcePort": sp, "target": dst, "targetPort": dp}


MAJORITY_CIRCUIT = {"version": 1, "parts": [
    part("a", "input", "A"), part("b", "input", "B"), part("c", "input", "C"),
    part("g1", "and", "AND"), part("g2", "and", "AND"), part("g3", "and", "AND"), part("or", "or", "OR", count=3),
    part("o", "output", "alarm")], "wires": [
    wire("a", "Q", "g1", "A0"), wire("b", "Q", "g1", "A1"), wire("b", "Q", "g2", "A0"), wire("c", "Q", "g2", "A1"),
    wire("a", "Q", "g3", "A0"), wire("c", "Q", "g3", "A1"), wire("g1", "Y", "or", "A0"), wire("g2", "Y", "or", "A1"),
    wire("g3", "Y", "or", "A2"), wire("or", "Y", "o", "D")]}


def show_submission(label: str, sub) -> None:
    print(f"  {label}: band={sub.band} evidence={sub.evidence} assessed_by={sub.assessed_by} model={sub.model}")
    print(f"    summary: {sub.summary}")
    if sub.check:
        print(f"    check: {sub.check.type} passed={sub.check.passed} — {sub.check.detail}")
        for m in sub.check.mismatches[:3]:
            print(f"      mismatch: {m}")
    if sub.card:
        print(f"    card.next_step: {sub.card.next_step}")
    if sub.tip:
        print(f"    tip: {sub.tip.text}")
    if sub.flags:
        print(f"    flags: {sub.flags}")


def show_next(view) -> None:
    n = view.next_question
    if n is None:
        print("  next question: none")
        return
    print(f"  next question: {n.key} ({n.subject}, {n.skill}, difficulty {n.difficulty}) why={n.why}")
    if n.focus:
        print(f"    focus: {n.focus}")
    print(f"    reason: {n.reason}")


async def run_attempt(svc, user, *, key, language, answer, follow_up_answer):
    print(f"\n=== {key} ({language}) mode=deep")
    view = await svc.start(user, question_key=key, mode="deep", language=language, self_confidence=3)
    aid = uuid.UUID(view.id)
    t = time.perf_counter()
    sub, view = await svc.submit(user, aid, answer, idempotency_key=f"{key}-{language}-main")
    print(f"  main answer evaluated in {time.perf_counter() - t:.0f}s, status={view.status}")
    show_submission("main", sub)
    turns = 0
    while view.pending_follow_up is not None:
        turns += 1
        print(f"  follow-up {turns} ({view.pending_follow_up.action}): {view.pending_follow_up.question}")
        t = time.perf_counter()
        fsub, view = await svc.submit(user, aid, follow_up_answer, idempotency_key=f"{key}-{language}-f{turns}",
                                      follow_up_turn=view.pending_follow_up.turn)
        print(f"  follow-up evaluated in {time.perf_counter() - t:.0f}s, status={view.status}")
        show_submission(f"follow-up {turns}", fsub)
    assert turns <= 1, f"{turns} follow-ups asked, expected at most one"
    print(f"  attempt status: {view.status}, follow-ups asked: {turns}")
    show_next(view)
    return view


async def main() -> None:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set")
    provider = build_provider("anthropic", api_key=settings.anthropic_api_key, model=settings.anthropic_model,
                              enable_fallbacks=settings.anthropic_enable_fallbacks, role_models=settings.role_models)
    catalog = load_catalog(settings.seeds_dir)
    store = InMemoryStore(catalog)
    svc = PracticeService(store, catalog, provider, ServiceConfig(polish_tips=True))
    user = uuid.uuid4()
    started = time.perf_counter()

    await run_attempt(svc, user, key="example-sensor-majority", language="en", answer=XOR_ANSWER,
                      follow_up_answer=FOLLOW_UP_ANSWER)
    await run_attempt(svc, user, key="example-count-set-bits", language="he", answer=HEBREW_CODE,
                      follow_up_answer="הבעיה היא range(31): הביט ה-32 לא נספר. צריך range(32) או לולאה עד ש-x מתאפס.")
    print("\n=== example-sensor-majority (en) drawn circuit, mode=deep")
    view = await svc.start(user, question_key="example-sensor-majority", mode="deep", language="en", self_confidence=4)
    sub, view = await svc.submit(user, uuid.UUID(view.id), {"text": "", "visual": {"circuit": MAJORITY_CIRCUIT, "images": []}},
                                 idempotency_key="circuit-main")
    show_submission("main (circuit only)", sub)
    while view.pending_follow_up is not None:
        print(f"  follow-up: {view.pending_follow_up.question}")
        fsub, view = await svc.submit(user, uuid.UUID(view.id), FOLLOW_UP_ANSWER, idempotency_key="circuit-f1",
                                      follow_up_turn=view.pending_follow_up.turn)
        show_submission("follow-up", fsub)
    show_next(view)

    progress = await svc.progress(user, language="en")
    print("\n=== progress")
    for s in progress.subjects:
        if s.attempts:
            print(f"  {s.key}: bands={s.bands} assessed={s.skills_assessed}/{s.skills_total} avg={s.average_level}")
    cost = sum(u["cost_usd"] for u in store.usage)
    print(f"\nTOTAL: {len(store.usage)} model calls, ${cost:.2f}, {time.perf_counter() - started:.0f}s wall")


if __name__ == "__main__":
    asyncio.run(main())
