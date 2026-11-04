"""Prepare guarded copy-only SQL from frozen backups. Never connects to a database.

Example (from the repository root):
  backend/.venv/Scripts/python.exe backend/scripts/prepare_question_copy_sync.py \
    --baseline HEAD --backups ../backups/question-copy-20261104 \
    --output ../backups/question-copy-20261104/prepared

The plan always records conflicts. SQL is emitted only for a conflict-free plan.
Review the rollback dry run, then the canary, then the remaining batches. Nothing
here executes SQL, inserts/deletes rows, changes identities, or grants approval.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SEEDS = ("backend/seeds/questions/example_bank.json", "backend/seeds/questions/preparation_bank.json")
LANGUAGES = {"he", "en"}
TEXT_FIELDS = {"title", "prompt", "requirements", "reference_solution", "hints", "common_errors", "accepted_approaches", "choices"}
TRANSLATION_COLUMNS = TEXT_FIELDS - {"title", "accepted_approaches"}
# Display fields are deliberately enumerated, rather than permitting arbitrary assets edits.
MATERIAL_FIELDS = {
    "assumptions", "optimality", "verification", "edge_cases", "interview_answer", "common_mistakes",
    "solution_extensions", "prompt_variants", "transition_tables", "truth_table", "waveform_observations",
    "fsm", "strategy", "source_ambiguities", "ambiguities", "solution_networks", "area_optimization",
    "technical_references", "component_truth_table", "circuit_interpretation", "network", "diagnostic_test",
    "answer_branches", "netlist", "netlists", "component_delays_ns", "retiming_alternative", "course_terminology",
    "terminology_clarification", "alternative_solution_notes", "descending_diagram_extension",
    "diagram_description", "driver_explanation_he", "eight_cell_alternative", "formula_interpretation",
    "group_logic_derivation_he", "group_logic_derivation_verification", "hierarchy_diagram_explanation_he",
    "n2_design_comparison", "original_formula_latex", "parallel_products_explanation", "part_5_cost_model",
    "part_6_two_level_explanation", "recursive_two_bit_alternative", "relationship_note", "solution_references",
    "solution_schematic_verification", "solution_gate_schematic_verification", "editorial_notes",
}
MISSING = object()
PROTECTED_BLOCKS = re.compile(r"```[^\n]*\n.*?```|\\\[.*?\\\]|\\\(.*?\\\)", re.DOTALL)


def differences(before: Any, after: Any, path: tuple = ()):
    """Yield the smallest stable paths, keeping resized arrays as atomic values."""
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(before.keys() | after.keys()):
            yield from differences(before.get(key, MISSING), after.get(key, MISSING), (*path, key))
    elif isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
        for index, (old, new) in enumerate(zip(before, after)):
            yield from differences(old, new, (*path, index))
    elif not same_value(before, after):
        yield path, before, after


def same_value(before: Any, after: Any) -> bool:
    # Python equates True with 1; JSON (and the database guard) does not.
    if before is MISSING or after is MISSING:
        return before is after
    return json.dumps(before, sort_keys=True, ensure_ascii=False) == json.dumps(after, sort_keys=True, ensure_ascii=False)


def at(value: Any, path: tuple):
    for part in path:
        if isinstance(value, dict):
            value = value.get(part, MISSING)
        elif isinstance(value, list) and isinstance(part, int) and 0 <= part < len(value):
            value = value[part]
        else:
            return MISSING
    return value


def set_path(value: dict, path: tuple, replacement: Any):
    parent = value
    for part in path[:-1]:
        if isinstance(parent, dict) and part not in parent:
            parent[part] = {}
        parent = parent[part]
    if replacement is MISSING:
        del parent[path[-1]]
    else:
        parent[path[-1]] = deepcopy(replacement)


def encoded(value: Any):
    return {"missing": True} if value is MISSING else {"value": value}


def text_copy_only(before: Any, after: Any) -> bool:
    """Allow copy/structure edits, but never change numerical/boolean technical data."""
    def contains_data(value):
        if isinstance(value, (int, float, bool)):
            return True
        if isinstance(value, dict):
            return any(contains_data(child) for child in value.values())
        if isinstance(value, list):
            return any(contains_data(child) for child in value)
        return False

    if contains_data(before) or contains_data(after):
        return False
    # Keep authored code and explicitly delimited math exact, even inside prose.
    def blocks(value):
        if isinstance(value, str):
            return PROTECTED_BLOCKS.findall(value)
        if isinstance(value, dict):
            return [block for child in value.values() for block in blocks(child)]
        if isinstance(value, list):
            return [block for child in value for block in blocks(child)]
        return []

    return blocks(before) == blocks(after)


def material_scope(path: tuple):
    if path[:2] != ("assets", "preparation_resource") or len(path) < 3:
        return None
    if path[2] in MATERIAL_FIELDS:
        return path[:3]
    if len(path) >= 4 and path[2] == "learner_material" and path[3] in MATERIAL_FIELDS:
        return path[:4]
    return None


def localized_material_preserves_data(before: Any, after: Any) -> bool:
    """Only language wrappers may move technical values; every other key/index stays fixed.

    Numeric/boolean cells and fenced code/math remain identical at their technical
    path. Duplicated language branches must agree. This is not a value multiset:
    swapping truth-table cells or moving a number to a different field is rejected.
    """
    def invariant_map(value):
        result = {}

        def walk(node, path=()):
            if isinstance(node, dict):
                for key, child in node.items():
                    walk(child, path if key in LANGUAGES else (*path, key))
            elif isinstance(node, list):
                for index, child in enumerate(node):
                    walk(child, (*path, index))
            elif isinstance(node, (int, float, bool)):
                result.setdefault((*path, "@number"), set()).add(json.dumps(node))
            elif isinstance(node, str):
                for index, block in enumerate(PROTECTED_BLOCKS.findall(node)):
                    result.setdefault((*path, "@block", index), set()).add(block)

        walk(value)
        return result

    def languages_agree(node):
        if isinstance(node, dict):
            branches = [invariant_map(node[language]) for language in sorted(LANGUAGES) if language in node]
            if branches and (len(branches) != 2 or branches[0] != branches[1]) and any(branches):
                return False
            return all(languages_agree(child) for child in node.values())
        if isinstance(node, list):
            return all(languages_agree(child) for child in node)
        return True

    original, localized = invariant_map(before), invariant_map(after)
    return (original == localized and all(len(values) == 1 for values in original.values())
            and any(path[-1] == "@number" for path in original) and languages_agree(after))


def allowed(path: tuple, before: Any, after: Any) -> bool:
    if len(path) >= 3 and path[0] == "translations":
        return path[1] in LANGUAGES and path[2] in TEXT_FIELDS and text_copy_only(before, after)
    if len(path) >= 3 and path[:2] == ("assets", "titles"):
        return len(path) == 3 and path[2] in LANGUAGES and isinstance(after, str)
    if len(path) == 4 and path[:2] == ("assets", "bank_media"):
        return isinstance(path[2], int) and path[3] == "caption" and isinstance(after, str)
    if path == ("assets", "solution_review"):
        return after is MISSING  # a changed revision can lose its attestation, never gain one
    if path[:2] == ("assets", "preparation_resource") and len(path) >= 3:
        relative = path[2:]
        if relative[0] in MATERIAL_FIELDS:
            return text_copy_only(before, after)
        if relative[0] == "learner_material" and len(relative) >= 2:
            return relative[1] in MATERIAL_FIELDS and text_copy_only(before, after)
        if len(relative) >= 3 and relative[0] == "translations":
            return relative[1] in LANGUAGES and relative[2] in TEXT_FIELDS | {"hint"} and text_copy_only(before, after)
        if relative == ("website_editorial", "learner_text_edited"):
            return isinstance(after, bool)
        if len(relative) == 3 and relative[0] == "media_assets":
            return isinstance(relative[1], int) and relative[2] == "caption" and isinstance(after, str)
    return False


def read_seed_pair(root: Path, revision: str):
    old, new = {}, {}
    for filename in SEEDS:
        baseline = json.loads(subprocess.check_output(["git", "show", f"{revision}:{filename}"], cwd=root))
        current = json.loads((root / filename).read_text(encoding="utf-8"))
        for destination, rows in ((old, baseline), (new, current)):
            for question in rows:
                if question["key"] in destination:
                    raise ValueError(f"Duplicate seed key: {question['key']}")
                destination[question["key"]] = question
    if old.keys() != new.keys():
        raise ValueError("Copy synchronization cannot add, remove, or rename questions")
    return old, new


def read_backups(directory: Path):
    entries, files = {}, []
    for path in sorted(directory.glob("before-*.json")):
        raw = path.read_bytes()
        files.append({"file": str(path), "sha256": hashlib.sha256(raw).hexdigest()})
        for entry in json.loads(raw):
            key = entry["question"]["key"]
            if key in entries:
                raise ValueError(f"Duplicate backed-up question: {key}")
            if not isinstance(entry.get("translations"), list) or not isinstance(entry.get("skills"), list):
                raise ValueError(f"Incomplete backup: {key}")
            entries[key] = entry
    if not files:
        raise ValueError("No before-*.json backup files found")
    return entries, files


def content_hash(question: dict) -> str:
    # Reuse the actual importer's fingerprint; importing it performs no I/O to a DB.
    sys.path.insert(0, str(ROOT / "backend"))
    sys.path.insert(0, str(ROOT / "backend/scripts"))
    from app.schemas.bank import BankQuestion
    from seed_db import content_hash as seed_content_hash
    return seed_content_hash(BankQuestion.model_validate(question))


def solution_hash(question: dict) -> str:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.engine.solution_review import solution_content_hash
    return solution_content_hash(question)


def build_plan(old: dict, new: dict, live: dict, hash_function=content_hash, solution_hash_function=solution_hash):
    items, conflicts, rejected = [], [], []
    changed_keys = []
    if old.keys() != new.keys():
        raise ValueError("Copy synchronization cannot add, remove, or rename questions")
    if old.keys() != live.keys():
        conflicts.append({"reason": "backup inventory differs from seed inventory",
                          "missing": sorted(old.keys() - live.keys()), "unexpected": sorted(live.keys() - old.keys())})
    for key in sorted(old):
        changes = list(differences(old[key], new[key]))
        if not changes:
            continue
        changed_keys.append(key)
        unsafe = []
        for path, previous, desired in changes:
            if allowed(path, previous, desired):
                continue
            scope = material_scope(path)
            if scope and localized_material_preserves_data(at(old[key], scope), at(new[key], scope)):
                continue
            unsafe.append((path, previous, desired))
        if unsafe:
            rejected.extend({"key": key, "path": list(path), "before": encoded(previous), "after": encoded(desired)}
                            for path, previous, desired in unsafe)
            continue
        if key not in live:
            conflicts.append({"key": key, "reason": "missing live row"})
            continue
        entry = live[key]
        before = entry["question"]
        translations = {row["language"]: row for row in entry["translations"]}
        if len(translations) != len(entry["translations"]) or set(translations) != set(old[key]["translations"]):
            conflicts.append({"key": key, "reason": "translation languages differ from baseline"})
            continue
        after = deepcopy(before)
        translated_after = deepcopy(translations)
        patches = []
        item_conflicts = []

        def patch(target: dict, path: tuple, previous: Any, desired: Any, source: tuple, language=None):
            actual = at(target, path)
            if not same_value(actual, previous):
                item_conflicts.append({"key": key, "language": language, "path": list(path), "source": list(source),
                                       "baseline": encoded(previous), "live": encoded(actual), "desired": encoded(desired)})
                return
            set_path(target, path, desired)
            patches.append({"table": "question_translation" if language else "question", "language": language,
                            "path": list(path), "before": encoded(actual), "after": encoded(desired)})

        for path, previous, desired in changes:
            if path == ("assets", "solution_review"):
                continue  # handled as one-way invalidations below
            if path[0] == "translations":
                _, language, field, *tail = path
                if field in TRANSLATION_COLUMNS:
                    patch(translated_after[language], (field, *tail), previous, desired, path, language)
                if language == "en" and field in {"requirements", "reference_solution", "hints", "accepted_approaches"}:
                    patch(after, (field, *tail), previous, desired, path)
                if language == "en" and field == "choices":
                    patch(after, ("choices", "options", *tail), previous, desired, path)
                if language == "en" and field == "common_errors":
                    if not tail:
                        item_conflicts.append({"key": key, "path": list(path), "reason": "common error mapping must be patched by existing key"})
                        continue
                    error_key = tail[0]
                    matches = [i for i, error in enumerate(after["common_errors"]) if error["key"] == error_key]
                    if len(matches) != 1:
                        item_conflicts.append({"key": key, "path": list(path), "reason": "missing or duplicate live common error key"})
                    else:
                        patch(after, ("common_errors", matches[0], "explanation", *tail[1:]), previous, desired, path)
                continue
            target_path = path
            if path[:2] == ("assets", "bank_media"):
                source_media = old[key]["assets"]["bank_media"][path[2]]
                matches = [i for i, media in enumerate(after["assets"].get("bank_media", []))
                           if all(media.get(field) == source_media.get(field) for field in ("source_path", "language", "role"))]
                if len(matches) != 1:
                    item_conflicts.append({"key": key, "path": list(path), "reason": "media identity differs or is ambiguous"})
                    continue
                target_path = ("assets", "bank_media", matches[0], "caption")
            patch(after, target_path, previous, desired, path)

        if item_conflicts:
            conflicts.extend(item_conflicts)
            continue
        # Calibration/readiness is independent of copy and solution approval: preserve it.
        # Only remove an attestation whose exact content fingerprint no longer matches.
        assets = after["assets"]
        live_review = assets.get("solution_review")
        if live_review is not None and (not isinstance(live_review, dict)
                                       or live_review.get("content_sha256") != solution_hash_function(new[key])):
            assets.pop("solution_review", None)
            patches.append({"table": "question", "language": None, "path": ["assets", "solution_review"],
                            "before": encoded(live_review), "after": encoded(MISSING), "reason": "stale attestation invalidated"})
        new_hash = hash_function(new[key])
        patches.append({"table": "question", "language": None, "path": ["assets", "content_hash"],
                        "before": encoded(assets.get("content_hash", MISSING)), "after": encoded(new_hash)})
        assets["content_hash"] = new_hash
        items.append({"key": key, "before": before, "after": after, "patches": patches,
                      "translations": [{"before": translations[language], "after": translated_after[language]}
                                       for language in sorted(translations)],
                      "skills": sorted(entry["skills"], key=lambda row: row["skill_id"])})
    return {"changed_seed_keys": changed_keys, "items": items, "conflicts": conflicts, "rejected_seed_changes": rejected}


def sql(items: list[dict], *, commit: bool = False) -> str:
    # The SQL uses complete snapshots for guards, but SET is restricted to copy fields.
    payload = json.dumps([{key: item[key] for key in ("key", "before", "after", "translations", "skills")} for item in items],
                         ensure_ascii=False, separators=(",", ":"))
    token = hashlib.sha256(payload.encode()).hexdigest()[:16]
    tag = f"$copy_payload_{token}$"
    block_tag = f"$question_copy_sync_{token}$"
    if tag in payload or block_tag in payload:
        raise ValueError("Payload delimiter collision")
    return """-- Prepared only. Review and run the dry-run before applying this transaction.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';
DO """ + block_tag + """
DECLARE
  changes jsonb := """ + tag + payload + tag + """::jsonb;
  item jsonb; trans jsonb; q public.question%ROWTYPE; proposed public.question%ROWTYPE;
  tr public.question_translation%ROWTYPE; proposed_tr public.question_translation%ROWTYPE;
  actual_skills jsonb; actual_translations integer; affected integer;
BEGIN
  FOR item IN SELECT value FROM jsonb_array_elements(changes) ORDER BY value->>'key' LOOP
    SELECT * INTO STRICT q FROM public.question
      WHERE key = item->>'key' AND id = (item->'before'->>'id')::uuid FOR UPDATE;
    IF (to_jsonb(q) - ARRAY['updated_at','times_served']) IS DISTINCT FROM
       ((item->'before') - ARRAY['updated_at','times_served']) THEN
      RAISE EXCEPTION 'Concurrent question change for %; transaction aborted', item->>'key';
    END IF;
    PERFORM 1 FROM public.question_skill WHERE question_id = q.id ORDER BY skill_id FOR SHARE;
    SELECT COALESCE(jsonb_agg(to_jsonb(s) ORDER BY s.skill_id), '[]'::jsonb) INTO actual_skills
      FROM public.question_skill s WHERE s.question_id = q.id;
    IF actual_skills IS DISTINCT FROM item->'skills' THEN
      RAISE EXCEPTION 'Concurrent skill links change for %; transaction aborted', item->>'key';
    END IF;
    PERFORM 1 FROM public.question_translation WHERE question_id = q.id ORDER BY language FOR UPDATE;
    SELECT count(*) INTO actual_translations FROM public.question_translation WHERE question_id = q.id;
    IF actual_translations <> jsonb_array_length(item->'translations') THEN
      RAISE EXCEPTION 'Translation count changed for %', item->>'key';
    END IF;
    FOR trans IN SELECT value FROM jsonb_array_elements(item->'translations') LOOP
      SELECT * INTO STRICT tr FROM public.question_translation
        WHERE question_id = q.id AND language::text = trans->'before'->>'language';
      IF (to_jsonb(tr) - 'updated_at') IS DISTINCT FROM ((trans->'before') - 'updated_at') THEN
        RAISE EXCEPTION 'Concurrent translation change for % / %', item->>'key', trans->'before'->>'language';
      END IF;
      IF trans->'before' IS DISTINCT FROM trans->'after' THEN
        proposed_tr := jsonb_populate_record(tr, trans->'after');
        UPDATE public.question_translation SET prompt = proposed_tr.prompt, requirements = proposed_tr.requirements,
          reference_solution = proposed_tr.reference_solution, hints = proposed_tr.hints,
          common_errors = proposed_tr.common_errors, choices = proposed_tr.choices
          WHERE question_id = q.id AND language = proposed_tr.language;
        GET DIAGNOSTICS affected = ROW_COUNT;
        IF affected <> 1 THEN RAISE EXCEPTION 'Unexpected translation update count'; END IF;
        SELECT * INTO STRICT tr FROM public.question_translation WHERE question_id = q.id AND language = proposed_tr.language;
        IF (to_jsonb(tr) - 'updated_at') IS DISTINCT FROM ((trans->'after') - 'updated_at') THEN
          RAISE EXCEPTION 'Unexpected translation postimage for %', item->>'key';
        END IF;
      END IF;
    END LOOP;
    proposed := jsonb_populate_record(q, item->'after');
    UPDATE public.question SET requirements = proposed.requirements, reference_solution = proposed.reference_solution,
      hints = proposed.hints, accepted_approaches = proposed.accepted_approaches,
      common_errors = proposed.common_errors, choices = proposed.choices, assets = proposed.assets
      WHERE id = q.id;
    GET DIAGNOSTICS affected = ROW_COUNT;
    IF affected <> 1 THEN RAISE EXCEPTION 'Unexpected question update count'; END IF;
    SELECT * INTO STRICT q FROM public.question WHERE id = q.id;
    IF (to_jsonb(q) - ARRAY['updated_at','times_served']) IS DISTINCT FROM
       ((item->'after') - ARRAY['updated_at','times_served']) THEN
      RAISE EXCEPTION 'Unexpected question postimage for %', item->>'key';
    END IF;
    SELECT COALESCE(jsonb_agg(to_jsonb(s) ORDER BY s.skill_id), '[]'::jsonb) INTO actual_skills
      FROM public.question_skill s WHERE s.question_id = q.id;
    IF actual_skills IS DISTINCT FROM item->'skills' THEN
      RAISE EXCEPTION 'Unexpected skill links postimage for %', item->>'key';
    END IF;
  END LOOP;
END;
""" + block_tag + """;
""" + ("COMMIT;\n" if commit else "ROLLBACK;\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="HEAD", help="Frozen commit containing the original seed copy")
    parser.add_argument("--backups", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="Directory outside the git repository")
    parser.add_argument("--canary", help="One changed question key; defaults to the first changed question")
    parser.add_argument("--batch-size", type=int, default=5)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.is_relative_to(ROOT.resolve()):
        parser.error("Backups and generated SQL must stay outside the git repository")
    if args.batch_size < 1 or args.batch_size > 100:
        parser.error("Batch size must be between 1 and 100")
    revision = subprocess.check_output(["git", "rev-parse", args.baseline], cwd=ROOT, text=True).strip()
    old, new = read_seed_pair(ROOT, revision)
    live, files = read_backups(args.backups.resolve())
    plan = build_plan(old, new, live)
    plan.update({"baseline_commit": revision, "prepared_at": datetime.now(timezone.utc).isoformat(), "backups": files,
                 "backup_question_count": len(live), "backup_skill_link_count": sum(len(x["skills"]) for x in live.values()),
                 "seed_files": [{"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for path in SEEDS]})
    digest = hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    output.mkdir(parents=True, exist_ok=True)
    prefix = output / f"copy-{digest}"
    plan_file = Path(f"{prefix}-plan.json")
    plan_file.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {"plan": str(plan_file), "changed_seed_questions": len(plan["changed_seed_keys"]), "planned_questions": len(plan["items"]),
               "conflicts": len(plan["conflicts"]), "rejected_seed_changes": len(plan["rejected_seed_changes"]), "sql": []}
    if summary["conflicts"] or summary["rejected_seed_changes"]:
        print(json.dumps(summary, ensure_ascii=False))
        return 2
    items = plan["items"]
    if items:
        canary_key = args.canary or items[0]["key"]
        canary = [item for item in items if item["key"] == canary_key]
        if len(canary) != 1:
            parser.error("Canary must be one of the changed question keys in the plan")
        remaining = [item for item in items if item["key"] != canary_key]
        groups = [("canary", canary)] + [(f"batch-{index // args.batch_size + 1:03d}", remaining[index:index + args.batch_size])
                                       for index in range(0, len(remaining), args.batch_size)]
        for name, group in groups:
            for commit in (False, True):
                path = Path(f"{prefix}-{name}-{'apply' if commit else 'dry-run'}.sql")
                path.write_text(sql(group, commit=commit), encoding="utf-8")
                summary["sql"].append({"file": str(path), "keys": [item["key"] for item in group], "commits": commit})
    summary_file = Path(f"{prefix}-manifest.json")
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
