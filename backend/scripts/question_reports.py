"""The review queue's inbox: what candidates said was unclear or wrong, per question.

    uv run python scripts/question_reports.py                     # open reports, grouped by question, most reported first
    uv run python scripts/question_reports.py --resolve <id> <id> --by harel   # mark reports handled

Reads the real database (DATABASE_URL). Shows the question key and title, the reason, the note, the language, where it
was pressed and when; never the reporter's e-mail.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app import db  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.repo import reports  # noqa: E402


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--resolve", nargs="*", help="report ids to mark as handled")
    parser.add_argument("--by", default=None, help="who handled them (required with --resolve)")
    args = parser.parse_args()
    settings = get_settings()
    if not settings.database_url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2
    engine = db.get_engine()
    async with engine.begin() as connection:
        if args.resolve:
            if not args.by:
                print("--by is required with --resolve", file=sys.stderr)
                return 2
            count = await reports.resolve(connection, [uuid.UUID(i) for i in args.resolve], by=args.by)
            print(f"resolved {count} report(s)")
            return 0
        rows = await reports.open_reports(connection)
        if not rows:
            print("no open reports" if await reports.available() else "the question_report table does not exist yet")
            return 0
        question = await db.table("question")
        ids = list({r["question_id"] for r in rows})
        names = {row.id: (row.key, row.assets or {}) for row in
                 (await connection.execute(select(question.c.id, question.c.key, question.c.assets).where(question.c.id.in_(ids))))}
        grouped: dict[uuid.UUID, list[dict]] = defaultdict(list)
        for r in rows:
            grouped[r["question_id"]].append(r)
        for qid, items in sorted(grouped.items(), key=lambda kv: -len(kv[1])):
            key, assets = names.get(qid, (str(qid), {}))
            titles = (assets or {}).get("titles") or {}
            print(f"\n{key}  ({len(items)} open)  {titles.get('he') or titles.get('en') or ''}")
            for r in items:
                when = r["created_at"].strftime("%Y-%m-%d %H:%M") if r.get("created_at") else ""
                print(f"  [{r['id']}] {r['reason']:<8} {r['language']} {r['context']:<9} {when}  {r['note'] or ''}")
    await engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
