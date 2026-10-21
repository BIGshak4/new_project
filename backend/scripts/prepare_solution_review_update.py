"""Prepare a guarded assets-only attestation update; never connect to a database.

Pass a private snapshot from SNAPSHOT_SQL and --output an ignored/private folder.
Check the project identity and save a complete content backup before executing
the generated SQL with the authenticated database tool. No import is needed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.engine.solution_review import solution_content_hash  # noqa: E402

SNAPSHOT_SQL = """select q.key, q.choices->'correct_index' as correct_choice,
jsonb_build_object('shared_code', q.assets->'shared_code', 'code_language', q.assets->'code_language',
'bank_media', q.assets->'bank_media', 'preparation_resource',
jsonb_build_object('learner_material', q.assets->'preparation_resource'->'learner_material')) as assets,
coalesce((select jsonb_object_agg(t.language::text, jsonb_build_object('prompt', t.prompt,
'reference_solution', coalesce(nullif(t.reference_solution,''),q.reference_solution), 'choices',t.choices))
from public.question_translation t where t.question_id=q.id),'{}'::jsonb) as translations
from public.question q where q.status in ('trial','published') order by q.key"""


def prepare(snapshot: list[dict], registry: dict) -> str:
    records = registry["questions"]
    if len(snapshot) != len({item["key"] for item in snapshot}) or not snapshot:
        raise ValueError("Snapshot must have distinct, nonempty question keys")
    updates = []
    for item in snapshot:
        record = records.get(item["key"])
        if not record or solution_content_hash(item) != record.get("content_sha256"):
            raise ValueError(f"No matching existing attestation: {item['key']}")
        updates.append({"expected": item, "review": record})
    delimiter = "$solution_review_20261021$"
    encoded = json.dumps(updates, ensure_ascii=False, separators=(",", ":"))
    if delimiter in encoded:
        raise ValueError("SQL delimiter collision")
    current = SNAPSHOT_SQL.rsplit("\nfrom public.question q where", 1)[0]
    return f"""-- Solution-correctness attestation only. Leaves review, parity, reuse and eligibility columns intact.
begin;
do $review_update$
declare
    item jsonb;
    locked_id uuid;
    current_content jsonb;
    changed integer := 0;
begin
    for item in select value from jsonb_array_elements({delimiter}{encoded}{delimiter}::jsonb)
    loop
        select q.id into strict locked_id from public.question q
        where q.key = item->'expected'->>'key' and q.status in ('trial','published') for update;
        -- Parent locking blocks new FK child inserts; existing translations need
        -- their own locks so reference edits cannot race the snapshot check.
        perform t.question_id from public.question_translation t
        where t.question_id = locked_id order by t.language for update;
        select to_jsonb(content_row) into current_content from (
            {current}
            from public.question q where q.id = locked_id
        ) content_row;
        if current_content is distinct from item->'expected' then
            raise exception 'Question content changed since attestation snapshot: %', item->'expected'->>'key';
        end if;
        update public.question set assets = jsonb_set(coalesce(assets, '{{}}'::jsonb),
            '{{solution_review}}', item->'review', true) where id = locked_id;
        changed := changed + 1;
    end loop;
    if changed <> {len(updates)} then
        raise exception 'Unexpected solution-review update count: %', changed;
    end if;
end
$review_update$;
commit;
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    registry = json.loads((BACKEND / "seeds/solution_review_attestations.json").read_text(encoding="utf-8"))
    sql = prepare(snapshot, registry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(sql, encoding="utf-8")
    print(f"Prepared {len(snapshot)} guarded metadata updates. No database writes were made: {args.output}")


if __name__ == "__main__":
    main()
