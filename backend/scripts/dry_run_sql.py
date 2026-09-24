"""Run a SQL script against the database inside a transaction that is ALWAYS rolled back,
then prove the rollback by checking that no table, column, index or policy the script
mentions exists afterwards.

    uv run python scripts/dry_run_sql.py ../supabase/migrations/2026..._something.sql

Why this exists: SQLAlchemy's asyncpg adapter sends BEGIN lazily, on the first statement
it runs itself. A script pushed through the raw driver connection before that point runs
in autocommit. This tool talks to asyncpg directly and opens the transaction explicitly,
so a "dry run" is a dry run.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402

CREATE_TABLE = re.compile(r"create\s+table\s+(?:if\s+not\s+exists\s+)?(?:public\.)?(\w+)", re.I)
CREATE_INDEX = re.compile(r"create\s+(?:unique\s+)?index\s+(?:if\s+not\s+exists\s+)?(\w+)", re.I)
CREATE_POLICY = re.compile(r"create\s+policy\s+\"([^\"]+)\"", re.I)
ADD_COLUMN = re.compile(r"alter\s+table\s+(?:public\.)?(\w+)(.*?);", re.I | re.S)
ADD_COLUMN_NAME = re.compile(r"add\s+column\s+(?:if\s+not\s+exists\s+)?(\w+)", re.I)


def created_objects(sql: str) -> dict[str, list]:
    columns = []
    for table, body in ADD_COLUMN.findall(sql):
        columns += [(table, column) for column in ADD_COLUMN_NAME.findall(body)]
    return {"tables": CREATE_TABLE.findall(sql), "indexes": CREATE_INDEX.findall(sql),
            "policies": CREATE_POLICY.findall(sql), "columns": columns}


async def leftovers(conn: asyncpg.Connection, objects: dict[str, list]) -> list[str]:
    found = []
    for table in objects["tables"]:
        if await conn.fetchval("select to_regclass($1) is not null", f"public.{table}"):
            found.append(f"table {table}")
    for index in objects["indexes"]:
        if await conn.fetchval("select count(*) from pg_indexes where indexname = $1", index):
            found.append(f"index {index}")
    for policy in objects["policies"]:
        if await conn.fetchval("select count(*) from pg_policies where policyname = $1", policy):
            found.append(f"policy {policy}")
    for table, column in objects["columns"]:
        exists = await conn.fetchval(
            "select count(*) from information_schema.columns where table_schema='public' and table_name=$1 and column_name=$2",
            table, column)
        if exists:
            found.append(f"column {table}.{column}")
    return found


def dsn() -> str:
    url = get_settings().database_url
    if not url:
        sys.exit("DATABASE_URL is not set in backend/.env")
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def dry_run(path: Path, checks: list[str], replaces: list[str]) -> int:
    sql = path.read_text(encoding="utf-8")
    objects = created_objects(sql)
    conn = await asyncpg.connect(dsn(), statement_cache_size=0)
    try:
        # an object the script drops and recreates (a policy rewritten in place) is expected to exist beforehand
        before = [item for item in await leftovers(conn, objects) if item not in replaces]
        if before:
            print("already present before the run (the script would fail or is already applied):")
            for item in before:
                print("  -", item)
            return 2
        transaction = conn.transaction()
        await transaction.start()
        try:
            await conn.execute(sql)
            print(f"script ran: {len(objects['tables'])} table(s), {len(objects['columns'])} column(s), "
                  f"{len(objects['indexes'])} index(es), {len(objects['policies'])} policy(ies)")
            for check in checks:
                rows = await conn.fetch(check)
                print(f"  check: {check}\n    -> {[dict(r) for r in rows][:5]}")
        finally:
            await transaction.rollback()
        after = [item for item in await leftovers(conn, objects) if item not in replaces]
        if after:
            print("ROLLBACK DID NOT HOLD, these exist now:")
            for item in after:
                print("  -", item)
            return 1
        print("rolled back; nothing the script creates exists. Dry run OK.")
        return 0
    finally:
        await conn.close()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Hebrew in --check output on a Windows console
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("script", type=Path)
    parser.add_argument("--check", action="append", default=[], help="a SELECT to run after the script, inside the transaction")
    parser.add_argument("--replaces", action="append", default=[],
                        help='an object the script drops and recreates, e.g. "policy learners upload answer images"')
    args = parser.parse_args()
    sys.exit(asyncio.run(dry_run(args.script, args.check, args.replaces)))


if __name__ == "__main__":
    main()
