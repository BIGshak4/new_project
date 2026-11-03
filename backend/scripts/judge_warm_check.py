"""Does warming the judge's prompt cache cut the verdict's time on the REAL model? (Shaked, 2026-11-02)

Takes a question with figures, then runs on the real provider (LLM_PROVIDER=openai):

    1. judge a canned answer with nothing warmed           -> cold latency, cached tokens
    2. send the warm-up (what the API now does on question open)
    3. judge the same canned answer again                   -> warm latency, cached tokens

and prints the figures' sizes before and after the 1024 px bound. Three judge calls and one warm-up: a few cents.
No database writes.

    uv run python scripts/judge_warm_check.py [--question prep-...] [--language en] [--passes 1]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from app.config import get_settings  # noqa: E402
from app.engine import bank, evaluator  # noqa: E402
from app.engine.catalog import load_catalog  # noqa: E402
from app.engine.warmup import JudgeWarmer, has_prompt_images  # noqa: E402
from app.runtime import REAL_PROVIDERS, make_provider  # noqa: E402
from app.services import question_resources  # noqa: E402

ANSWER = ("I would write the truth table from the requirement, derive the simplified expression, and check the boundary "
          "cases. The enable gates the next-state logic and the synchronous reset has priority over everything else.")


async def judge(provider, catalog, question, language, label):
    skill = catalog.skills[question.primary_skill]
    images = await question_resources.fetch_question_images(question) or []
    started = time.perf_counter()
    result = await evaluator.evaluate(provider, question_context=evaluator.question_block(question, language, skill),
                                      known_error_keys={e.key for e in question.common_errors}, language=language,
                                      difficulty=question.difficulty, answer=ANSWER, glossary=catalog.glossary,
                                      question_images=images)
    wall = time.perf_counter() - started
    usage = result.usage
    band = result.evaluation.rubric_level_estimate if result.evaluation else None
    print(f"  {label:<22} {wall:5.1f} s wall · model {result.latency_ms} ms · input {usage.input_tokens} uncached + "
          f"{usage.cache_read_tokens} cached · out {usage.output_tokens} · ${usage.cost_usd(result.model) or 0:.4f} · "
          f"level {band} · flags {result.flags}")
    return wall, usage.cache_read_tokens


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", default=None, help="question key; default: the first question with figures")
    parser.add_argument("--language", default="en", choices=("en", "he"))
    parser.add_argument("--passes", type=int, default=1, help="repeat the cold/warm pair this many times")
    args = parser.parse_args()
    settings = get_settings()
    if settings.llm_provider not in REAL_PROVIDERS:
        raise SystemExit("set LLM_PROVIDER=openai with its key in backend/.env")
    provider = make_provider(settings)
    catalog = load_catalog(settings.seeds_dir)
    bank.ASSESS_UNREVIEWED_QUESTIONS = True
    for q in catalog.questions.values():
        bank.apply_readiness(q.assets)
    question = (catalog.questions[args.question] if args.question
                else next(q for q in catalog.questions.values() if has_prompt_images(q)))
    print(f"question {question.key} · difficulty {question.difficulty} · figures {len(question.assets.get('bank_media', []))}")

    media = [m for m in question.assets.get("bank_media", []) if m.get("role") == "prompt" and m.get("kind") == "image"]
    if media:
        raw = await question_resources._download(settings, media)
        shrunk = await question_resources.fetch_question_images(question) or []
        for (mime, data), (mime2, data2) in zip(raw, shrunk, strict=True):
            print(f"  figure {mime} {len(data):>9,} bytes -> {mime2} {len(data2):>9,} bytes")

    warmer = JudgeWarmer(provider, fetch_images=question_resources.fetch_question_images, glossary=catalog.glossary)
    for n in range(args.passes):
        print(f"\npass {n + 1}")
        await judge(provider, catalog, question, args.language, "cold (no warm-up)")
        started = time.perf_counter()
        ok = await warmer.warm(question, args.language, catalog.skills[question.primary_skill])
        print(f"  {'warm-up':<22} {time.perf_counter() - started:5.1f} s · taken {ok} · stats {warmer.stats}")
        await judge(provider, catalog, question, args.language, "after the warm-up")
        if n + 1 < args.passes:
            print("  (waiting 11 minutes for the cache to expire would make the next pass cold again; not waiting)")


if __name__ == "__main__":
    asyncio.run(main())
