"""The founders' soft-skill report: the seven soft skills, their improvement, and the overall gradient per pilot user.

Backend-only data by Shaked's decision (2026-10-18): nothing of this reaches the API or the screens. Reads the
real database read-only through the same service the API uses; writes nothing.

    cd backend && uv run python scripts/soft_skills_report.py            # every user with scored answers
    uv run python scripts/soft_skills_report.py --user <uuid> --json out.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import dispose, get_engine  # noqa: E402
from app.runtime import build_runtime  # noqa: E402


async def users_with_answers() -> list[tuple[uuid.UUID, str]]:
    engine = get_engine()
    async with engine.connect() as c:
        await c.execute(text("set transaction read only"))
        rows = (await c.execute(text("""
            select a.user_id, coalesce(max(p.display_name), 'user') as name, count(*) as answers
            from attempt a join attempt_submission s on s.attempt_id = a.id
            left join user_profile p on p.id = a.user_id
            where s.status = 'done' and s.band is not null
            group by a.user_id order by answers desc"""))).all()
    return [(r.user_id, r.name) for r in rows]


def line(s: dict) -> str:
    level = (s["level"] or {}).get("en", "too early") if s["level"] else "too early"
    # the gradient is shown only once the word is meaningful (10 relevant answers); before that it misleads
    gradient = "—" if s["gradient"] is None or s["improvement"] == "too_early" else f"{s['gradient']:+.1f}/10 answers"
    counts = f"answers={s['answers']:<3} (gradient on {s.get('gradient_answers', 0)})"
    return f"  {s['label']['en']:26} {level:16} {s['improvement']:18} {counts} {gradient}"


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--user", type=uuid.UUID, help="one user id; default: every user with scored answers")
    parser.add_argument("--json", type=Path, help="also write the full result here (a bare file name lands in backend/workdir/, "
                                                   "which git ignores: the file holds user ids)")
    args = parser.parse_args()
    runtime = build_runtime(get_settings())            # the API's own wiring: database store, read through the same service
    practice = runtime.practice
    try:
        targets = [(args.user, "user")] if args.user else await users_with_answers()
        results = []
        for user_id, name in targets:
            result = await practice.soft_skills(user_id)
            result["name"] = name
            results.append(result)
            overall = result["overall"]
            figure = "—" if overall["gradient"] is None else f"{overall['gradient']:+.1f}/10 answers"
            print(f"\n== {name} ({str(user_id)[:8]}) — {result['answers_read']} answers read, "
                  f"overall: {overall['improvement']} ({figure}, {overall['skills_judged']} skills judged)")
            for s in result["soft_skills"]:
                print(line(s))
            judged = {k: g for k, g in result["hard_skills"].items() if g["improvement"] != "too_early"}
            if judged:
                print("  hard skills with a gradient: " + ", ".join(f"{k} {g['gradient']:+.1f}/10 ({g['improvement']})"
                                                                    for k, g in sorted(judged.items())))
        if args.json:
            target = args.json if args.json.parent != Path(".") else Path(__file__).resolve().parent.parent / "workdir" / args.json
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            print(f"\nwritten: {target}")
    finally:
        await runtime.aclose()
        await dispose()


if __name__ == "__main__":
    asyncio.run(main())
