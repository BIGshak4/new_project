"""A whole mock interview on the REAL model, without database writes (in-memory store).

Answers alternate between a good and a weak canned reply so the router has something to react to.
Prints each turn (skill, difficulty, question, hidden band), the closing report, timings and cost.
The seed bank is still in review, so reviewed_only is switched off here; production keeps it on.

    uv run python scripts/e2e_mock_interview.py [--duration 20] [--language en]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.engine.catalog import load_catalog  # noqa: E402
from app.engine.providers import build_provider  # noqa: E402
from app.services.interview_service import InterviewConfig, InterviewService  # noqa: E402
from app.services.memory_store import InMemoryStore  # noqa: E402

GOOD = ("I would start from the requirement, write the truth table or the state list, derive the simplified "
        "expression or the code, and check it on the boundary cases. For this question: {hint}")
WEAK = "I am not sure. I think it is just an XOR of the inputs, or maybe an OR; I would need to look it up."


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=20, choices=(20, 30, 45))
    parser.add_argument("--language", default="en", choices=("en", "he"))
    args = parser.parse_args()
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set")
    provider = build_provider("anthropic", api_key=settings.anthropic_api_key, model=settings.anthropic_model,
                              enable_fallbacks=settings.anthropic_enable_fallbacks, role_models=settings.role_models)
    catalog = load_catalog(settings.seeds_dir)
    store = InMemoryStore(catalog)
    svc = InterviewService(store, catalog, provider, InterviewConfig(reviewed_only=False, narrative=True))
    user = uuid.uuid4()
    started = time.perf_counter()

    view = await svc.start(user, duration_min=args.duration, language=args.language)
    sid = uuid.UUID(view.id)
    print(f"interview {sid} · {args.duration} min · plan: {', '.join(p.skill for p in view.plan)}")
    n = 0
    while view.status == "in_progress" and view.current_turn is not None and n < 12:
        turn = view.current_turn
        n += 1
        print(f"\n[{turn.index}] {turn.skill_label} (d{turn.difficulty}, {turn.archetype}) — {turn.question_key}")
        print("    Q:", " ".join(turn.question.split())[:160])
        if view.can_hint and n == 2:
            hint, view = await svc.hint(user, sid)
            print("    hint:", hint.text[:120] if hint else None)
        answer = WEAK if n % 3 == 0 else GOOD.format(hint=catalog.questions[turn.question_key].text(args.language).reference_solution[:200])
        t = time.perf_counter()
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
    print("  next:", [s.label for s in report.recommended_next_skills][:4])
    print("\n" + report.narrative_md[:1200])
    cost = sum(u["cost_usd"] for u in store.usage)
    print(f"\nTOTAL: {len(store.usage)} model calls, ${cost:.2f}, {time.perf_counter() - started:.0f}s wall")


if __name__ == "__main__":
    asyncio.run(main())
