"""Move questions between review states without writing SQL.

    uv run python scripts/question_status.py --list
    uv run python scripts/question_status.py --set trial example-sensor-majority example-mod-six-counter
    uv run python scripts/question_status.py --set published --reviewed-by "Harel Artman" example-sensor-majority
    uv run python scripts/question_status.py --set in_review example-sensor-majority

Without --apply the script only prints what would change. Every --apply is a change to the live database:
run it only when both founders agree on the list.

States: in_review (development only) -> trial (served to pilot users, badged "on trial", used by the coach and
the mock interview) -> published (requires --reviewed-by; sets reviewed_at and reuse_status=permitted when it was
still pending). withheld / retired take a question out of service.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, update  # noqa: E402

from app import db  # noqa: E402
from app.repo import cache  # noqa: E402

STATES = ("draft", "in_review", "trial", "published", "withheld", "retired")


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("keys", nargs="*", help="question keys, e.g. example-sensor-majority")
    parser.add_argument("--list", action="store_true", help="show every question with its status")
    parser.add_argument("--set", choices=STATES, help="the new status for the given keys")
    parser.add_argument("--reviewed-by", help="required with --set published: who reviewed the question")
    parser.add_argument("--apply", action="store_true", help="write the change (otherwise a dry run)")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    question = await db.table("question")
    async with db.get_engine().begin() as connection:
        rows = (await connection.execute(
            select(question.c.key, question.c.status, question.c.reviewed_by, question.c.reuse_status)
            .order_by(question.c.status, question.c.key))).all()
        by_key = {r.key: r for r in rows}
        if args.list or not args.set:
            width = max(len(r.key) for r in rows) if rows else 20
            for r in rows:
                print(f"  {r.key:<{width}}  {r.status:<10}  reuse={r.reuse_status:<20}  reviewed_by={r.reviewed_by or '-'}")
            counts = {}
            for r in rows:
                counts[r.status] = counts.get(r.status, 0) + 1
            print("\n  " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
            if not args.set:
                return 0
        if not args.keys:
            print("no question keys given")
            return 2
        unknown = [k for k in args.keys if k not in by_key]
        if unknown:
            print("unknown keys:", ", ".join(unknown))
            return 2
        if args.set == "published" and not args.reviewed_by:
            print("--set published needs --reviewed-by \"Name\" (the person who checked the question)")
            return 2

        values: dict = {"status": args.set}
        if args.set == "published":
            values["reviewed_by"] = args.reviewed_by
            values["reviewed_at"] = datetime.now(UTC)
        print(f"\n{'APPLYING' if args.apply else 'DRY RUN'}: {len(args.keys)} question(s) -> {args.set}")
        for key in args.keys:
            current = by_key[key]
            extra = ""
            if args.set == "published" and current.reuse_status == "pending_review":
                extra = " (reuse_status pending_review -> permitted)"
            print(f"  {key}: {current.status} -> {args.set}{extra}")
        if not args.apply:
            print("\nadd --apply to write this to the database")
            return 0
        for key in args.keys:
            row_values = dict(values)
            if args.set == "published" and by_key[key].reuse_status == "pending_review":
                row_values["reuse_status"] = "permitted"
            await connection.execute(update(question).where(question.c.key == key).values(**row_values))
    cache.clear()
    print("done; the API picks the change up within a minute (question cache)")
    await db.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
