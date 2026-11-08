"""Sync compiled bank difficulty into the linked JobRun database, preserving all other content.

Run from a checkout with Supabase CLI v3 installed and authenticated:
    python backend/scripts/sync_question_difficulty.py          # update, verify and roll back
    python backend/scripts/sync_question_difficulty.py --apply  # verify again, back up and commit

Every run checks both translations, including the effective reference answer used by
the backend. A stale stored seed hash is not itself evidence that the live text differs.
A transaction guard covers all question and translation columns through commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from seed_db import content_hash

from app.config import get_settings
from app.engine.question_difficulty import RATINGS, difficulty_fingerprint
from app.schemas.bank import BankQuestion

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "djpwvqpsqbkvprlncjjg"

# Store a digest of all durable question fields other than the ones we are updating.
# updated_at is maintained by a trigger; the engine increments times_served independently.
# The translation digest covers the raw rows, including parity/review metadata.
SNAPSHOT = """
select q.id, q.key, q.difficulty,
       q.assets -> 'difficulty_status' as difficulty_status,
       q.assets ? 'difficulty_status' as had_status,
       q.assets -> 'content_hash' as content_hash, q.assets ? 'content_hash' as had_hash,
       md5(((to_jsonb(q) - array['difficulty','assets','times_served','updated_at'])
             || jsonb_build_object('assets', q.assets - array['difficulty_status','content_hash']))::text) as protected,
       md5(t.raw::text) as translation_hash,
       md5(q.requirements) as base_requirements, md5(q.reference_solution) as base_answer,
       md5(q.assets->>'shared_code') as shared_code, q.choices->'correct_index' as correct_choice,
       array(select m->>'sha256' from jsonb_array_elements(q.assets->'bank_media') m
             where m->>'role'='prompt' order by m->>'sha256') as prompt_media,
       q.assets->>'source_sha256' as source_sha256, t.texts,
       (select jsonb_object_agg(s.key, jsonb_build_object('weight', l.weight, 'primary', l.is_primary))
        from public.question_skill l join public.skill s on s.id=l.skill_id where l.question_id=q.id) as skills,
       (select key from public.skill where id=q.subject_id) as subject,
       (select coalesce(jsonb_agg(jsonb_build_object('key', e->'key','core',e->'core',
                    'skill',e->'skill','tip_key',tp.key) order by ord), '[]'::jsonb)
        from jsonb_array_elements(q.common_errors) with ordinality as errors(e,ord)
        left join public.tips_library tp on tp.id=(e->>'tip_id')::uuid) as common_errors
from public.question q
left join lateral (
    select jsonb_agg(to_jsonb(tr) order by tr.language) as raw,
           jsonb_object_agg(tr.language::text, jsonb_build_object(
               'title', md5(q.assets->'titles'->>tr.language::text),
               'prompt', md5(tr.prompt),
               'requirements', md5(coalesce(nullif(tr.requirements,''),q.requirements)),
               'reference_solution', md5(coalesce(nullif(tr.reference_solution,''),q.reference_solution)),
               'choices', tr.choices
           )) as texts
    from public.question_translation tr where tr.question_id=q.id
) t on true
"""


def query(cli: str, sql: str, *, read_only: bool = False) -> list[dict]:
    # A SQL file also avoids leaking data into the process list or hitting argument size limits.
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "difficulty.sql"
        source.write_text(sql, encoding="utf-8")
        command = [cli, "db", "query", f"--remote={PROJECT}", "--file", str(source), "--output-format", "json"]
        command.append("--read-only" if read_only else "--yes")
        run = subprocess.run(command, cwd=ROOT, capture_output=True, encoding="utf-8")
    if run.returncode:
        raise RuntimeError(run.stderr.strip() or run.stdout.strip())
    return json.loads(run.stdout).get("rows", [])


def text_hash(value: str) -> str:
    # PostgreSQL md5(text) encodes UTF-8 just like the local seeds.
    return hashlib.md5(value.encode("utf-8"), usedforsecurity=False).hexdigest()


def check_stale_hashes(cli: str, stale: dict[str, dict], questions: dict[str, BankQuestion]) -> None:
    """Prove that reseeding these rows would change only the reviewed rating metadata.

    A prior intake can leave the old seed fingerprint stale. Compare the remaining
    raw grading fields it covers instead of trusting the stamp. assessment_ready
    is separately managed live and must survive, like the solution attestation.
    """
    keys = sorted(stale)
    for start in range(0, len(keys), 6):
        batch = keys[start:start + 6]
        clause = ",".join("'" + key.replace("'", "''") + "'" for key in batch)
        actual = query(cli, f"""
            select q.key, q.format::text, to_jsonb(q.practice_modes) as practice_modes,
                   q.assets->>'archetype' as archetype,
                   q.assets - array['content_hash','solution_review','difficulty_status',
                                    'assessment_ready','archetype'] as assets,
                   q.deterministic_check, q.rubric->'criteria' as rubric, q.accepted_approaches,
                   (select jsonb_object_agg(t.language::text, jsonb_build_object(
                        'hints',t.hints,'common_errors',t.common_errors))
                    from public.question_translation t where t.question_id=q.id) as grading,
                   md5(((to_jsonb(q) - array['difficulty','assets','times_served','updated_at'])
                        || jsonb_build_object('assets',q.assets - array['difficulty_status','content_hash']))::text)
                        as protected,
                   (select md5(jsonb_agg(to_jsonb(t) order by t.language)::text)
                    from public.question_translation t where t.question_id=q.id) as translation_hash
            from public.question q where q.key in ({clause})
        """, read_only=True)
        if {row["key"] for row in actual} != set(batch):
            raise ValueError("Questions changed during the grading check")
        for row in actual:
            key = row["key"]
            question = questions[key]
            prior = stale[key]
            expected = {
                "protected": prior["protected"], "translation_hash": prior["translation_hash"],
                "format": question.format, "practice_modes": question.practice_modes,
                "archetype": question.archetype.value, "deterministic_check": question.deterministic_check,
                "rubric": [c.model_dump() for c in question.rubric],
                "accepted_approaches": question.text("en").accepted_approaches,
                "grading": {lang: {"hints": t.hints, "common_errors": t.common_errors}
                            for lang, t in question.translations.items()},
            }
            if question.assets.get("preparation_id"):
                expected["assets"] = {k: v for k, v in question.assets.items()
                                      if k not in {"difficulty_status", "assessment_ready", "solution_review",
                                                   "content_hash", "archetype"}}
            mismatches = [k for k, value in expected.items() if row[k] != value]
            if mismatches:
                raise ValueError(f"{key}: stale seed hash and different live fields: {mismatches}")


def plan_updates(cli: str, rows: list[dict], questions: dict[str, BankQuestion]) -> list[dict]:
    live = {r["key"] for r in rows}
    if not rows or len(rows) != len(live) or live != questions.keys():
        raise ValueError(f"Catalog mismatch: {len(rows)} live, {len(questions)} compiled; "
                         f"missing live={sorted(questions.keys() - live)}, extra live={sorted(live - questions.keys())}")
    differences = []
    stale = {}
    plan = []
    for row in rows:
        key = row["key"]
        question = questions[key]
        if question.assets.get("difficulty_status") != "rated":
            raise ValueError(f"Compiled question has no reviewed difficulty: {key}")
        texts = row["texts"] or {}
        if set(texts) != {"en", "he"} or set(question.translations) != {"en", "he"}:
            differences.append(f"{key}: missing or extra translation")
        for lang, item in question.translations.items():
            if (texts.get(lang) or {}).get("choices") != item.choices:
                differences.append(f"{key}: {lang}.choices")
            for field in ("title", "prompt", "requirements", "reference_solution"):
                if (texts.get(lang) or {}).get(field) != text_hash(getattr(item, field)):
                    differences.append(f"{key}: {lang}.{field}")
        for live_field, value in (("base_requirements", question.text("en").requirements),
                                  ("base_answer", question.text("en").reference_solution)):
            if row[live_field] != text_hash(value):
                differences.append(f"{key}: {live_field}")
        code = question.assets.get("shared_code")
        expected = {"source_sha256": question.assets.get("source_sha256"),
                    "shared_code": None if code is None else text_hash(code),
                    "prompt_media": sorted(m["sha256"] for m in question.assets.get("bank_media", [])
                                           if m["role"] == "prompt"),
                    "correct_choice": question.correct_choice, "subject": question.subject,
                    "skills": {s.skill: {"weight": s.weight, "primary": s.primary} for s in question.skills},
                    "common_errors": [e.model_dump() for e in question.common_errors]}
        differences.extend(f"{key}: {k}" for k, value in expected.items() if row[k] != value)
        prior_seed = question.model_copy(deep=True)
        prior_seed.difficulty = row["difficulty"]
        if row["had_status"]:
            prior_seed.assets["difficulty_status"] = row["difficulty_status"]
        else:
            prior_seed.assets.pop("difficulty_status", None)
        if content_hash(prior_seed) != row["content_hash"]:
            stale[key] = row
        # Pin the full checked snapshot so a concurrent edit between preflight and writing
        # aborts instead of silently pairing a rating with a different revision.
        plan.append({"prior": row, "difficulty": question.difficulty, "hash": content_hash(question)})
    if differences:
        raise ValueError("Live and compiled content differ:\n" + "\n".join(differences))
    check_stale_hashes(cli, stale, questions)
    print(f"Existing seed fingerprints: {len(rows)-len(stale)} match; "
          f"independently checked grading fields on {len(stale)} outdated fingerprints.", flush=True)
    return plan


def update_sql(plan: list[dict], *, apply: bool) -> str:
    delimiter = "$question_rating_plan$"
    payload = json.dumps(plan, ensure_ascii=False, separators=(",", ":"))
    if delimiter in payload:
        raise ValueError("Unexpected SQL delimiter in input")
    return f"""
begin;
set local lock_timeout = '8s';
set local statement_timeout = '60s';
-- Keep the checked key set stable, including new questions/translation inserts.
lock table public.question, public.question_translation in share row exclusive mode;
lock table public.question_skill, public.skill, public.tips_library in share mode;
do $sync$
declare
    plan jsonb := {delimiter}{payload}{delimiter}::jsonb;
    conflict text;
begin
    with checked as ({SNAPSHOT}), desired as (
        select item->'prior' as prior from jsonb_array_elements(plan) as item
    )
    select coalesce(c.key, d.prior->>'key') into conflict from checked c
    full join desired d on d.prior->>'key' = c.key
    where to_jsonb(c) is distinct from d.prior limit 1;
    if found then raise exception 'Bank changed since backup: %', conflict; end if;

    update public.question q set difficulty=(d.item->>'difficulty')::smallint,
        assets=q.assets || jsonb_build_object('difficulty_status','rated','content_hash',d.item->>'hash')
    from jsonb_array_elements(plan) as d(item)
    where q.id=(d.item->'prior'->>'id')::uuid and
        (q.difficulty, q.assets->>'difficulty_status', q.assets->>'content_hash') is distinct from
        ((d.item->>'difficulty')::smallint, 'rated'::text, d.item->>'hash');

    with checked as ({SNAPSHOT}), desired as (
        select (item->'prior') || jsonb_build_object('difficulty', item->'difficulty',
            'difficulty_status', 'rated', 'had_status', true,
            'content_hash', item->>'hash', 'had_hash', true) as expected
        from jsonb_array_elements(plan) as item
    )
    select coalesce(c.key, d.expected->>'key') into conflict from checked c
    full join desired d on d.expected->>'key' = c.key
    where to_jsonb(c) is distinct from d.expected limit 1;
    if found then raise exception 'Post-update verification failed: %', conflict; end if;
end $sync$;
{"commit" if apply else "rollback"};
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--cli", default=shutil.which("supabase"), help="path to the Supabase CLI v3 executable")
    args = parser.parse_args()
    if not args.cli:
        parser.error("Install Supabase CLI v3 or supply --cli with the executable path")
    linked = ROOT / "supabase/.temp/project-ref"
    if not linked.is_file() or linked.read_text().strip() != PROJECT:
        raise ValueError(f"This checkout is not linked to the expected JobRun project {PROJECT}")
    questions = {}
    ratings = json.loads(RATINGS.read_text(encoding="utf-8"))
    for path in sorted((get_settings().seeds_dir / "questions").glob("*.json")):
        entries = json.loads(path.read_text(encoding="utf-8"))
        for record in entries if isinstance(entries, list) else [entries]:
            question = BankQuestion.model_validate(record)
            if question.key in questions:
                raise ValueError(f"Duplicate compiled key: {question.key}")
            rating = ratings.get(question.key) or {}
            if (rating.get("content_sha256") != difficulty_fingerprint(record)
                    or type(rating.get("difficulty")) is not int or rating["difficulty"] != question.difficulty
                    or not (rating.get("reason") or "").strip()):
                raise ValueError(f"{question.key}: compiled difficulty or content disagrees with review manifest")
            questions[question.key] = question
    if set(questions) != set(ratings):
        raise ValueError("Review manifest and compiled catalog have different keys")
    rows = query(args.cli, SNAPSHOT + " order by q.key", read_only=True)
    plan = plan_updates(args.cli, rows, questions)
    changed = sum((p["prior"]["difficulty"], p["prior"]["difficulty_status"], p["prior"]["content_hash"])
                  != (p["difficulty"], "rated", p["hash"]) for p in plan)
    print(f"{PROJECT}: verified {len(plan)} questions and both languages; {changed} metadata updates.", flush=True)
    if args.apply:
        directory = ROOT.parent / "backups"
        directory.mkdir(exist_ok=True)
        backup = directory / ("question-difficulty-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
        with backup.open("x", encoding="utf-8") as handle:
            json.dump({"project": PROJECT, "before": rows}, handle, ensure_ascii=False, indent=2)
        print(f"Saved prior values and protected-column fingerprints to {backup}", flush=True)
    query(args.cli, update_sql(plan, apply=args.apply))
    print("Committed and verified all rows." if args.apply else "Dry run verified all rows and rolled back.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as exc:
        sys.exit(str(exc))
