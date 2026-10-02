"""Add/update only prepared questions and private, content-addressed assets.

Default: validate, report, and run SQL in a rolled-back transaction. --apply uploads
assets first, verifies their hashes, backs up existing content outside Git, then commits.
No question, solution, history, drawing or learner record is deleted.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from seed_db import REPORT, seed_questions  # noqa: E402

from app import db  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.engine.catalog import load_catalog  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


class Rollback(Exception):
    pass


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    catalog = load_catalog(settings.seeds_dir)
    catalog.questions = {k: q for k, q in catalog.questions.items() if q.assets.get("preparation_id")}
    if len(catalog.questions) != 37:
        raise ValueError("Expected the audited 37-question archive; review the import before changing this guard.")
    manifest = json.loads((settings.seeds_dir / "preparation_uploads.json").read_text(encoding="utf-8"))
    for spec in manifest["files"].values():
        path = (ROOT / "interview_preparation" / spec["local_path"]).resolve()
        if not path.is_relative_to((ROOT / "interview_preparation").resolve()):
            raise ValueError("Asset is outside the archive")
        if hashlib.sha256(path.read_bytes()).hexdigest() != spec["sha256"]:
            raise ValueError(f"Asset changed: {spec['local_path']}; rebuild before importing")
    if args.apply:
        base = settings.supabase_url.rstrip("/")
        headers = {"Authorization": f"Bearer {settings.supabase_service_role_key}", "apikey": settings.supabase_service_role_key}
        async with httpx.AsyncClient(headers=headers, timeout=45) as client:
            for i, (path, spec) in enumerate(manifest["files"].items(), 1):
                data = (ROOT / "interview_preparation" / spec["local_path"]).read_bytes()
                url = f"{base}/storage/v1/object/{manifest['bucket']}/{path}"
                existing = await client.get(url)
                if existing.status_code == 200:
                    if hashlib.sha256(existing.content).hexdigest() != spec["sha256"]:
                        raise ValueError(f"Content-addressed storage collision: {path}")
                else:
                    if existing.status_code not in (400, 404):
                        raise ValueError(f"Storage read failed with status {existing.status_code}")
                    response = await client.post(url, content=data, headers={
                        "Content-Type": "image/png" if path.endswith(".png") else "text/plain"})
                    if response.status_code not in (200, 201):
                        raise ValueError(f"Upload failed: {path} ({response.status_code})")
                    check = await client.get(url)
                    if check.status_code != 200 or hashlib.sha256(check.content).hexdigest() != spec["sha256"]:
                        raise ValueError(f"Upload verification failed: {path}")
                if i % 20 == 0 or i == len(manifest["files"]):
                    print(f"Verified {i}/{len(manifest['files'])} private assets", flush=True)
    tables = {name: await db.table(name) for name in ("question", "question_translation", "question_skill", "skill", "tips_library")}
    try:
        async with db.get_engine().begin() as conn:
            before = {r.key: str(r.id) for r in (await conn.execute(select(tables["question"].c.key, tables["question"].c.id))).all()}
            if args.apply:
                snapshot = {}
                for name in ("question", "question_translation", "question_skill"):
                    snapshot[name] = [dict(row._mapping) for row in await conn.execute(select(tables[name]))]
                target = ROOT.parent / "backups" / ("before-preparation-import-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S") + ".json")
                target.parent.mkdir(exist_ok=True)
                target.write_text(json.dumps(snapshot, ensure_ascii=False, default=str, indent=2), encoding="utf-8")
                print(f"Content backup: {target}", flush=True)
            skills = {r.key: r.id for r in await conn.execute(select(tables["skill"].c.key, tables["skill"].c.id))}
            tips = {r.key: r.id for r in await conn.execute(select(tables["tips_library"].c.key, tables["tips_library"].c.id))}
            counts = await seed_questions(conn, tables, catalog, skills, tips)
            after = {r.key: str(r.id) for r in (await conn.execute(select(tables["question"].c.key, tables["question"].c.id))).all()}
            if any(after.get(k) != v for k, v in before.items()):
                raise ValueError("An existing question was removed or its identity changed; rollback")
            if not set(catalog.questions).issubset(after):
                raise ValueError("Missing imported question; rollback")
            print(json.dumps({"applied": args.apply, "before": len(before), "after": len(after), **counts}), flush=True)
            print("\n".join(REPORT), flush=True)
            if not args.apply:
                raise Rollback
    except Rollback:
        print("Dry run rolled back; no database rows changed.")
    finally:
        await db.get_engine().dispose()


if __name__ == "__main__":
    asyncio.run(main())
