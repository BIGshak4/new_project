"""Check the question drafts that already wait in seeds/question_drafts/ before a person reviews them.

    uv run python scripts/verify_drafts.py --skills testbench_basics hdl_sequential_coding --out workdir/drafts.json

For every draft whose primary skill is asked for: the loader's own rules (shape, skills, tips, both languages, the
check against its own good and bad answers), then today's judge grades the draft's English reference solution. A
reference the judge does not call STRONG means the question or its reference is unclear, and the draft is not ready.
Real model calls (about half a cent a draft); nothing touches the database and no draft is changed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.engine.catalog import load_catalog  # noqa: E402
from app.runtime import make_provider  # noqa: E402
from app.schemas.bank import BankQuestion  # noqa: E402
from scripts.generate_questions import OUTPUT, SEEDS, validate, verify_reference  # noqa: E402


def primary(question: dict) -> str:
    return next(s["skill"] for s in question["skills"] if s.get("primary"))


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skills", nargs="+", required=True)
    parser.add_argument("--drafts", type=Path, default=OUTPUT)
    parser.add_argument("--out", type=Path, help="write the per-draft result as JSON")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--no-judge", action="store_true", help="the loader's rules only, no model call")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    catalog = load_catalog(SEEDS)
    drafts = [q for q in json.loads(args.drafts.read_text(encoding="utf-8")) if primary(q) in args.skills]
    taken = set(catalog.questions)
    provider = None if args.no_judge else make_provider(get_settings())
    gate = asyncio.Semaphore(args.concurrency)

    async def check(question: dict) -> dict:
        row = {"key": question["key"], "skill": primary(question), "difficulty": question["difficulty"],
               "format": question["format"], "title": question["translations"]["en"]["title"],
               "problems": validate(question, catalog), "band": None, "summary": None}
        if question["key"] in taken:
            row["problems"].append("a question with this key is already in the bank")
        # a code check is never run on this machine (no isolated runner here): that is not a defect of the draft
        row["code_check_not_run"] = (question.get("deterministic_check") or {}).get("type") == "code_tests"
        if row["code_check_not_run"]:
            row["problems"] = [p for p in row["problems"] if "self-test answer" not in p]
        if provider is not None and not any(p.startswith("shape") for p in row["problems"]):
            async with gate:
                try:
                    row["band"], row["summary"] = await verify_reference(provider, BankQuestion.model_validate(question), catalog)
                except Exception as exc:                        # noqa: BLE001 - reported per draft
                    row["band"], row["summary"] = "FAILED", f"{type(exc).__name__}: {exc}"[:200]
        return row

    rows = await asyncio.gather(*(check(q) for q in drafts))
    print(f"{len(rows)} drafts for {', '.join(args.skills)}\n")
    print("| skill | drafts | rules pass | reference STRONG | ready (both) |")
    print("|---|---:|---:|---:|---:|")
    for skill in args.skills:
        mine = [r for r in rows if r["skill"] == skill]
        clean = [r for r in mine if not r["problems"]]
        strong = [r for r in mine if r["band"] == "STRONG"]
        print(f"| {skill} | {len(mine)} | {len(clean)} | {len(strong)} | {len([r for r in clean if r['band'] == 'STRONG'])} |")
    print("\nbands:", dict(Counter(r["band"] for r in rows)))
    for r in rows:
        if r["problems"] or r["band"] != "STRONG":
            print(f"- {r['key']} (d{r['difficulty']}, {r['format']}): band {r['band']}"
                  + (f"; {'; '.join(r['problems'])[:300]}" if r["problems"] else "")
                  + (f" | judge: {r['summary']}" if r["band"] not in ("STRONG", None) else ""))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
