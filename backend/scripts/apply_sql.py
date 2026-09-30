"""Apply a SQL script to the database, in one transaction, after `dry_run_sql.py` passed and the founder approved it.

    uv run python scripts/apply_sql.py ../supabase/migrations/2026..._something.sql --yes

The MCP `apply_migration` tool is the usual path; this is the fallback for when that tool is not available. It uses
the backend's DATABASE_URL, opens the transaction explicitly (asyncpg, not the lazy SQLAlchemy adapter), runs the
script, commits, and prints the tables and indexes the script mentions with whether they now exist.
"""
from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402

try:
    import asyncpg
except ImportError:  # pragma: no cover
    print("asyncpg is required", file=sys.stderr)
    raise


def mentioned(sql: str, kind: str) -> list[str]:
    pattern = {"table": r"create table (?:if not exists )?(?:public\.)?(\w+)", "index": r"create (?:unique )?index (?:if not exists )?(\w+)"}[kind]
    return re.findall(pattern, sql, flags=re.IGNORECASE)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("script", type=Path)
    parser.add_argument("--yes", action="store_true", help="the founder approved this script after a dry run")
    args = parser.parse_args()
    if not args.yes:
        print("refusing without --yes (dry-run first: scripts/dry_run_sql.py)", file=sys.stderr)
        return 2
    sql = args.script.read_text(encoding="utf-8")
    url = get_settings().database_url
    if not url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    connection = await asyncpg.connect(url, timeout=30)
    try:
        transaction = connection.transaction()
        await transaction.start()
        try:
            await connection.execute(sql)
            await transaction.commit()
        except Exception:
            await transaction.rollback()
            raise
        for name in mentioned(sql, "table"):
            exists = await connection.fetchval("select to_regclass($1) is not null", f"public.{name}")
            print(f"table {name}: {'exists' if exists else 'MISSING'}")
        for name in mentioned(sql, "index"):
            exists = await connection.fetchval("select to_regclass($1) is not null", f"public.{name}")
            print(f"index {name}: {'exists' if exists else 'MISSING'}")
    finally:
        await connection.close()
    print("applied and committed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
