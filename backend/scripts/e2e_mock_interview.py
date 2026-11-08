"""A whole mock interview on the REAL model (LLM_PROVIDER=openai, fallback anthropic), without database writes (in-memory store).

Answers alternate between a good and a weak canned reply so the router has something to react to.
Prints each turn (skill, question, hidden band), the closing report, timings and cost.
The seed bank is still in review, so reviewed_only is switched off here; production keeps it on.

    uv run python scripts/e2e_mock_interview.py [--duration 20] [--language en]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")          # Windows consoles default to cp1252; the output has arrows and Hebrew

from app.config import get_settings  # noqa: E402
from app.engine import bank  # noqa: E402
from app.engine.catalog import load_catalog  # noqa: E402
from app.runtime import REAL_PROVIDERS, make_provider  # noqa: E402
from app.services.interview_service import InterviewConfig, InterviewService  # noqa: E402
from app.services.memory_store import InMemoryStore  # noqa: E402

GOOD = ("I would start from the requirement, write the truth table or the state list, derive the simplified "
        "expression or the code, and check it on the boundary cases. For this question: {hint}")
WEAK = "I am not sure. I think it is just an XOR of the inputs, or maybe an OR; I would need to look it up."


class FastClock:
    """Moves the interview clock by a fixed number of minutes per answer, so a whole interview ends by time in a
    few real minutes (the engine's END, the closing question and the time-up rules all run)."""

    def __init__(self, minutes_per_answer: float):
        self.now = datetime.now(UTC)
        self.step = timedelta(minutes=minutes_per_answer)

    def __call__(self):
        return self.now

    def advance(self):
        self.now += self.step


async def one_interview(svc, store, catalog, user, args, label: str) -> None:
    started = time.perf_counter()
    view = await svc.start(user, duration_min=args.duration, language=args.language)
    sid = uuid.UUID(view.id)
    print(f"\n##### {label}: interview {sid} · {args.duration} min · plan: {', '.join(p.skill for p in view.plan)}")
    n = 0
    while view.status == "in_progress" and view.current_turn is not None and n < 12:
        turn = view.current_turn
        n += 1
        tags = (" · CLOSING QUESTION" if turn.closing else "") + (f" · hint with the question (level {turn.hints[0].level})"
                                                                 if turn.hints else "")
        print(f"\n[{turn.index}] {turn.skill_label} ({turn.archetype}) — {turn.question_key}{tags}")
        print("    Q:", " ".join(turn.question.split())[:160])
        if turn.hints:
            print("    nudge:", turn.hints[0].text[:120])
        if view.can_hint and n == 2 and not turn.hints:
            hint, view = await svc.hint(user, sid)
            print("    hint asked for:", hint.text[:120] if hint else None)
        kind = args.pattern[(n - 1) % len(args.pattern)].upper()
        answer = WEAK if kind == "W" else GOOD.format(hint=catalog.questions[turn.question_key].text(args.language).reference_solution[:200])
        t = time.perf_counter()
        if hasattr(svc.clock, "advance"):
            svc.clock.advance()
        result, view = await svc.answer(user, sid, turn.index, answer, idempotency_key=f"t{turn.index}")
        stored = store.sessions[sid]["turns"][turn.index]["question_generation_meta"]
        print(f"    evaluated in {time.perf_counter() - t:.0f}s → {stored.get('band')} → {stored.get('action_after')}"
              f" | remaining {view.remaining_min} min | status {view.status}")
    if view.status == "in_progress":
        view = await svc.end(user, sid)
        print("\nended early after", n, "turns")
    t = time.perf_counter()
    report = await svc.report(user, sid)
    print(f"\n=== report ({time.perf_counter() - t:.0f}s, narrative {report.narrative_source})")
    for scope, fit in report.fit.items():
        print(f"  {scope}: fit={fit.fit_score} assessed={fit.skills_assessed}/{fit.skills_total} core_gaps={fit.core_gaps}")
    for s in report.skills:
        if s.status != "not_assessed":
            print(f"  {s.label}: {s.status} level={s.proficiency_level}/{s.required_level} turns={s.turns_count}")
    print("  held up:", [s.label for s in report.held_up])
    print("  next:", [s.label for s in report.recommended_next_skills][:4])
    if report.next_step:
        print(f"  next time: {report.next_step.step}, {report.next_step.duration_min} min, "
              f"practise {[s.label for s in report.next_step.skills]}")
    print("  since last time:", [(c.label, c.change, c.before, c.after) for c in report.since_last_time],
          "| fit", report.fit_change, "| previous", report.previous_session_id)
    print("  coins for finishing:", report.completion_coins, "| closing turns:", [t.index for t in report.turns if t.closing])
    print("\n" + report.narrative_md[:1600])
    cost = sum(u["cost_usd"] for u in store.usage)
    print(f"\n{label} TOTAL so far: {len(store.usage)} model calls, ${cost:.2f}, {time.perf_counter() - started:.0f}s wall")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=20, choices=(20, 30, 45))
    parser.add_argument("--language", default="en", choices=("en", "he"))
    parser.add_argument("--pattern", default="GGW", help="answers in order, cycling: G good, W weak (default GGW)")
    parser.add_argument("--minutes-per-answer", type=float, default=0,
                        help="move the interview clock this many minutes per answer (0: real time, the interview "
                             "is ended early after 12 questions)")
    parser.add_argument("--twice", action="store_true", help="run a second interview for the same user: the report "
                                                             "then says what changed since the first")
    args = parser.parse_args()
    settings = get_settings()
    if settings.llm_provider not in REAL_PROVIDERS:
        raise SystemExit("set LLM_PROVIDER=openai (or anthropic) with its key in backend/.env")
    provider = make_provider(settings)                          # openai or anthropic, by LLM_PROVIDER
    catalog = load_catalog(settings.seeds_dir)
    bank.ASSESS_UNREVIEWED_QUESTIONS = settings.assess_unreviewed_questions
    for question in catalog.questions.values():
        bank.apply_readiness(question.assets)
    store = InMemoryStore(catalog)
    svc = InterviewService(store, catalog, provider, InterviewConfig(reviewed_only=False, narrative=True))
    if args.minutes_per_answer:
        svc.clock = FastClock(args.minutes_per_answer)
    user = uuid.uuid4()
    started = time.perf_counter()
    await one_interview(svc, store, catalog, user, args, "first")
    if args.twice:
        if hasattr(svc.clock, "advance"):
            svc.clock.advance()
        await one_interview(svc, store, catalog, user, args, "second")
    cost = sum(u["cost_usd"] for u in store.usage)
    print(f"\nTOTAL: {len(store.usage)} model calls, ${cost:.2f}, {time.perf_counter() - started:.0f}s wall")


if __name__ == "__main__":
    asyncio.run(main())
