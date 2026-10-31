"""How fast, how cheap and how consistent is the judge under each speed setting? (Shaked, 2026-11-01: "lower the times")

    uv run python scripts/judge_speed_matrix.py                       # every configuration below, two passes each
    uv run python scripts/judge_speed_matrix.py --configs sol-low,terra-minimal --passes 1
    uv run python scripts/judge_speed_matrix.py --concurrency 1       # strictly one call at a time

The thirteen review answers (scripts/p2_review_set.py) go through the evaluator only, nothing is written to the
database, and the bands are compared with the human expectation written beside each answer and with the first
configuration's bands (the production setting). Two passes per configuration: the second shows whether OpenAI's
prompt cache is catching the instructions (cached tokens > 0) and what a warm answer costs.

Needs OPENAI_API_KEY in backend/.env. Nothing here changes a setting: the table is for Shaked to choose from, and the
choice is then OPENAI_MODEL / OPENAI_ROLE_EFFORT / OPENAI_SERVICE_TIER on Render.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.engine import evaluator, scores  # noqa: E402
from app.engine.catalog import load_catalog  # noqa: E402
from app.engine.checks import run_check  # noqa: E402
from app.engine.params import DEFAULT_PARAMS  # noqa: E402
from app.engine.providers import OpenAIProvider  # noqa: E402

HERE = Path(__file__).resolve().parent
SEEDS = HERE.parent / "seeds"

# label -> (judge model, evaluator effort, service tier). The first row is production as deployed on 2026-10-31.
CONFIGS: dict[str, tuple[str, str, str | None]] = {
    # "minimal" is refused by both models (400, probed 2026-11-01); "none" exists on terra only, sol starts at "low".
    "sol-low": ("gpt-6.1-sol", "low", None),
    "terra-low": ("gpt-6.1-terra", "low", None),
    "terra-none": ("gpt-6.1-terra", "none", None),
    "sol-low-priority": ("gpt-6.1-sol", "low", "priority"),
    "terra-low-priority": ("gpt-6.1-terra", "low", "priority"),
    "terra-none-priority": ("gpt-6.1-terra", "none", "priority"),
}


def load_cases():
    spec = importlib.util.spec_from_file_location("p2_review_set", HERE / "p2_review_set.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CASES


def agrees(expected: str, got: str) -> bool:
    return got in expected.split("/")


async def one_case(provider, cat, case, semaphore):
    key, language, expected, kind, answer, _ = case
    q = cat.questions[key]
    skill = cat.leaf_skills[q.primary_skill]
    check = run_check(q.deterministic_check, answer) if q.deterministic_check else None
    async with semaphore:
        t = time.perf_counter()
        r = await evaluator.evaluate(provider, question_context=evaluator.question_block(q, language, skill),
                                     known_error_keys={e.key for e in q.common_errors}, language=language,
                                     difficulty=q.difficulty, answer=answer, check=check, glossary=cat.glossary)
        seconds = time.perf_counter() - t
    row = {"key": key, "kind": kind, "expected": expected, "seconds": round(seconds, 1), "ok": r.ok,
           "usd": round(r.usage.cost_usd(r.model) or 0.0, 4), "cached": r.usage.cache_read_tokens, "tier": r.usage.service_tier,
           "tokens_in": r.usage.input_tokens, "tokens_out": r.usage.output_tokens, "band": None, "misconceptions": []}
    if r.ok:
        ev = scores.apply_check_result(r.evaluation, check, DEFAULT_PARAMS)
        core = bool(set(ev.misconceptions) & q.core_misconception_keys)
        row["band"] = scores.classify_band(ev, core, DEFAULT_PARAMS).value
        row["misconceptions"] = sorted(ev.misconceptions)
        row["correctness"] = round(ev.correctness, 2)
    else:
        row["flags"] = list(r.flags)
    return row


async def run_config(label, model, effort, tier, cases, cat, api_key, passes, concurrency):
    provider = OpenAIProvider(api_key=api_key, model=model, role_effort={"evaluator": effort}, service_tier=tier)
    results = []
    for n in range(1, passes + 1):
        semaphore = asyncio.Semaphore(concurrency)
        rows = await asyncio.gather(*[one_case(provider, cat, c, semaphore) for c in cases])
        results.append(rows)
        ok = [r for r in rows if r["ok"]]
        secs = sorted(r["seconds"] for r in ok) or [0.0]
        print(f"  pass {n}: {len(ok)}/{len(rows)} scored, median {statistics.median(secs):.1f}s, "
              f"p90 {secs[int(0.9 * (len(secs) - 1))]:.1f}s, ${sum(r['usd'] for r in ok) / max(len(ok), 1):.4f} per answer, "
              f"cached tokens avg {sum(r['cached'] for r in ok) / max(len(ok), 1):.0f}", flush=True)
        for r in rows:
            if not r["ok"]:
                print(f"    FAILED {r['key']} ({r['kind']}): {r.get('flags')}")
    return results


def summarise(label, results, cases, baseline_bands):
    final = results[-1]
    ok = [r for r in final if r["ok"]]
    secs = sorted(r["seconds"] for r in ok) or [0.0]
    expected_hits = sum(1 for r in ok if agrees(r["expected"], r["band"]))
    moved = [r for r in ok if baseline_bands.get(r["key"] + r["kind"]) not in (None, r["band"])]
    return {"config": label, "scored": f"{len(ok)}/{len(cases)}", "median_s": round(statistics.median(secs), 1),
            "p90_s": secs[int(0.9 * (len(secs) - 1))], "usd_per_answer": round(sum(r["usd"] for r in ok) / max(len(ok), 1), 4),
            "cold_usd_per_answer": round(sum(r["usd"] for r in results[0] if r["ok"]) / max(len(ok), 1), 4),
            "matches_expectation": f"{expected_hits}/{len(ok)}", "bands_moved_vs_production": len(moved),
            "moved": [f"{r['kind']}: {baseline_bands.get(r['key'] + r['kind'])} -> {r['band']}" for r in moved],
            "cached_tokens_avg_warm": round(sum(r["cached"] for r in ok) / max(len(ok), 1))}


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--configs", default=",".join(CONFIGS), help="comma-separated labels from CONFIGS")
    parser.add_argument("--passes", type=int, default=2)
    parser.add_argument("--concurrency", type=int, default=3, help="answers in flight per configuration")
    parser.add_argument("--out", default=str(HERE.parent / "workdir" / "judge_speed_matrix.json"))
    args = parser.parse_args()
    s = get_settings()
    if not s.openai_api_key:
        raise SystemExit("OPENAI_API_KEY is empty in backend/.env; the matrix calls the real model")
    labels = [c.strip() for c in args.configs.split(",") if c.strip()]
    unknown = [c for c in labels if c not in CONFIGS]
    if unknown:
        raise SystemExit(f"unknown configuration(s) {unknown}; known: {', '.join(CONFIGS)}")
    cases = load_cases()
    cat = load_catalog(SEEDS)
    print(f"{len(cases)} answers x {len(labels)} configurations x {args.passes} passes, {args.concurrency} in flight")
    all_results, summaries, baseline_bands = {}, [], {}
    for label in labels:
        model, effort, tier = CONFIGS[label]
        print(f"\n== {label}: judge {model}, effort {effort}, tier {tier or 'default'}", flush=True)
        try:
            results = await run_config(label, model, effort, tier, cases, cat, s.openai_api_key, args.passes, args.concurrency)
        except Exception as exc:                                     # one refused configuration must not end the night
            print(f"  configuration failed: {type(exc).__name__}: {str(exc)[:200]}")
            summaries.append({"config": label, "error": f"{type(exc).__name__}: {str(exc)[:200]}"})
            continue
        all_results[label] = results
        if not baseline_bands:
            baseline_bands = {r["key"] + r["kind"]: r["band"] for r in results[-1] if r["ok"]}
        summaries.append(summarise(label, results, cases, baseline_bands))
    print("\n== summary (last pass = warm cache) ==")
    header = ("config", "scored", "median_s", "p90_s", "usd_per_answer", "cold_usd_per_answer", "matches_expectation",
              "bands_moved_vs_production", "cached_tokens_avg_warm")
    print(" | ".join(header))
    for row in summaries:
        print(" | ".join(str(row.get(h, row.get("error", "-"))) for h in header))
        for m in row.get("moved", []):
            print(f"    moved: {m}")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"ran_at": datetime.now(UTC).isoformat(), "passes": args.passes, "concurrency": args.concurrency,
                               "summary": summaries, "results": all_results}, indent=1), encoding="utf-8")
    print(f"\nwritten: {out}")


if __name__ == "__main__":
    asyncio.run(main())
