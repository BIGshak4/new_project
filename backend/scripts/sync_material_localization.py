"""Patch only bilingual learner explanations on existing preparation questions.

Default is read-only. --apply backs up the affected content outside Git and updates
only preparation_resource.learner_material plus updated_at in one transaction.
Question IDs, versions, review state, original text, media and learner data stay intact.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

from sqlalchemy import select, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import db  # noqa: E402
from app.config import get_settings  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def database_belongs_to_project(database_url: str, project_ref: str) -> bool:
    try:
        parsed = urlparse(database_url)
        host = (parsed.hostname or "").lower()
        return host == f"db.{project_ref}.supabase.co" or (
            host.endswith(".pooler.supabase.com") and unquote(parsed.username or "") == f"postgres.{project_ref}")
    except ValueError:
        return False


def patch_for(live: dict, compiled: dict) -> dict:
    expected = compiled["assets"]
    resource = live.get("preparation_resource")
    if not isinstance(resource, dict):
        raise ValueError("Existing question has no preparation resource")
    if (live.get("preparation_id") != expected["preparation_id"]
            or live.get("source_sha256") != expected["source_sha256"]
            or resource.get("id") != expected["preparation_id"]):
        raise ValueError("Existing archive identity differs; no content was changed")
    return expected["preparation_resource"]["learner_material"]


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--project-ref", required=True)
    args = parser.parse_args()
    settings = get_settings()
    if urlparse(settings.supabase_url).hostname != f"{args.project_ref}.supabase.co":
        raise ValueError("Configured Supabase project does not match the requested project")
    if not database_belongs_to_project(settings.database_url, args.project_ref):
        raise ValueError("Configured database does not match the requested Supabase project")
    compiled = json.loads((ROOT / "backend/seeds/questions/preparation_bank.json").read_text(encoding="utf-8"))
    if len(compiled) != 48 or len({q["key"] for q in compiled}) != 48:
        raise ValueError("Expected the complete 48-question preparation archive")
    expected = {q["key"]: q for q in compiled}
    table = await db.table("question")
    try:
        async with db.get_engine().begin() as connection:
            query = select(table).where(table.c.key.in_(expected))
            if args.apply:
                query = query.with_for_update()
            before = {r["key"]: dict(r) for r in (await connection.execute(query)).mappings()}
            if set(before) != set(expected):
                raise ValueError("One or more existing question identities are missing")
            patches = {key: patch_for(row["assets"], expected[key]) for key, row in before.items()}
            changed = [key for key, row in before.items()
                       if row["assets"]["preparation_resource"].get("learner_material") != patches[key]]
            backup_path = None
            if args.apply and changed:
                backup_path = ROOT.parent / "backups" / (
                    "before-material-localization-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f") + ".json")
                backup_path.parent.mkdir(exist_ok=True)
                backup_path.write_text(json.dumps(before, ensure_ascii=False, default=str, indent=2) + "\n",
                                       encoding="utf-8")
                for key in changed:
                    await connection.execute(text("""
                        update public.question
                        set assets = jsonb_set(assets, '{preparation_resource,learner_material}',
                                               cast(:material as jsonb), true), updated_at = now()
                        where id = :id and key = :key
                    """), {"material": json.dumps(patches[key], ensure_ascii=False), "id": before[key]["id"], "key": key})
                after = {r["key"]: dict(r) for r in (await connection.execute(query)).mappings()}
                for key, old in before.items():
                    new = after[key]
                    expected_assets = {**old["assets"], "preparation_resource": {
                        **old["assets"]["preparation_resource"], "learner_material": patches[key]}}
                    if new["assets"] != expected_assets:
                        raise ValueError("Content verification failed; transaction rolled back")
                    for column in old.keys() - {"assets", "updated_at"}:
                        if new[column] != old[column]:
                            raise ValueError("An unrelated question field changed; transaction rolled back")
        print(json.dumps({"applied": args.apply, "questions_checked": len(before), "questions_changed": len(changed),
                          "bilingual_fields": sum(len(v) for v in patches.values()),
                          "backup": str(backup_path) if backup_path else None}))
    finally:
        await db.get_engine().dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as error:
        # Connection errors can include SQL or connection details; never log credentials/content.
        print(f"Localization sync did not commit ({type(error).__name__}).", file=sys.stderr)
        sys.exit(1)
