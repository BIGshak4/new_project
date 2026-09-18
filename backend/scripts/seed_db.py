"""Validate the seed files and load them into Supabase.

    uv run python scripts/seed_db.py --check     # validate only, no database needed
    uv run python scripts/seed_db.py             # validate, then upsert everything

Every row is upserted by its stable key, so the command can be run again after
editing a seed file. Nothing is deleted. Questions keep the status in their seed
file; only `published` questions are ever served to users.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.dialects.postgresql import insert  # noqa: E402

from app import db  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.engine.catalog import Catalog, CatalogError, load_catalog  # noqa: E402
from app.repo import cache  # noqa: E402

# what a reviewer decides in the database; an unchanged question keeps these across re-imports
REVIEW_COLUMNS = ("status", "reviewed_by", "reviewed_at", "review_notes", "reuse_status")
REPORT: list[str] = []


def content_hash(question) -> str:
    """Fingerprint of everything a reviewer approves. Metadata such as status or times_served is excluded."""
    import hashlib
    import json

    payload = {
        "format": question.format, "practice_modes": sorted(question.practice_modes), "subject": question.subject,
        "difficulty": question.difficulty, "archetype": question.archetype.value,
        "skills": [s.model_dump() for s in question.skills], "rubric": [c.model_dump() for c in question.rubric],
        "common_errors": [e.model_dump() for e in question.common_errors],
        "deterministic_check": question.deterministic_check, "correct_choice": question.correct_choice,
        "translations": {lang: t.model_dump(exclude={"parity_checked", "parity_checked_by"})
                         for lang, t in sorted(question.translations.items())},
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]


async def upsert(connection, table, rows: list[dict], conflict: list[str], *, returning: str | None = "id",
                 key: str | None = None) -> dict:
    """Insert or update by `conflict` columns. Returns {key value: id} when `key` is given."""
    ids: dict = {}
    for row in rows:
        statement = insert(table).values(**db.sql_values(row))       # None -> SQL NULL, never jsonb null
        updates = {c: statement.excluded[c] for c in row if c not in conflict}
        statement = (statement.on_conflict_do_update(index_elements=conflict, set_=updates) if updates
                     else statement.on_conflict_do_nothing(index_elements=conflict))
        if returning:
            statement = statement.returning(table.c[returning])
        result = await connection.execute(statement)
        if returning and key:
            value = result.scalar_one_or_none()
            if value is None:       # DO NOTHING returns no row
                value = (await connection.execute(select(table.c[returning]).where(table.c[key] == row[key]))).scalar_one()
            ids[row[key]] = value
    return ids


class DryRun(Exception):
    """Raised at the end of a dry run to roll the transaction back."""


async def seed(catalog: Catalog, *, dry_run: bool = False) -> dict[str, int]:
    counts: dict[str, int] = {}
    REPORT.clear()
    t = {name: await db.table(name) for name in (
        "skill", "skill_dependency", "role_template", "role_skill_set", "company_profile", "company_evidence",
        "company_skill_set", "question", "question_skill", "question_translation", "tips_library", "term_glossary")}

    try:
        async with db.get_engine().begin() as connection:
            counts = await _seed_in(connection, t, catalog)
            if dry_run:
                raise DryRun
    except DryRun:
        pass
    cache.clear()                                  # a running API must not serve the old ids or content
    return counts


async def _seed_in(connection, t: dict, catalog: Catalog) -> dict[str, int]:
    counts: dict[str, int] = {}
    # ---- skills: domains first so leaves can point at them
    def skill_row(skill, parent_id=None):
        return {"key": skill.key, "label": skill.label, "description": skill.description or skill.label,
                "node_type": skill.node_type, "parent_id": parent_id, "family": skill.family,
                "category": skill.category,
                "default_assessment_mode": skill.default_assessment_mode.value if skill.default_assessment_mode and skill.node_type == "skill" else None,
                "min_difficulty": skill.min_difficulty, "max_difficulty": skill.max_difficulty,
                "proficiency_rubric": skill.proficiency_rubric}
    skill_ids = await upsert(connection, t["skill"], [skill_row(s) for s in catalog.domains.values()], ["key"], key="key")
    skill_ids |= await upsert(connection, t["skill"],
                              [skill_row(s, skill_ids[s.subject]) for s in catalog.leaf_skills.values()], ["key"], key="key")
    counts["skill"] = len(skill_ids)
    dependencies = [{"skill_id": skill_ids[s.key], "prerequisite_skill_id": skill_ids[p], "strength": 0.5}
                    for s in catalog.leaf_skills.values() for p in s.prerequisites]
    await upsert(connection, t["skill_dependency"], dependencies, ["skill_id", "prerequisite_skill_id"], returning=None)
    counts["skill_dependency"] = len(dependencies)
    # ---- roles
    role_ids: dict[str, object] = {}
    for role in catalog.roles.values():
        row = {"slug": role.slug, "title": role.title, "family": role.family, "sub_family": role.sub_family,
               "description": role.description, "origin": "system", "version": role.version,
               "seniority_profiles": {k: v.model_dump() for k, v in role.seniority_profiles.items()},
               "question_archetypes": role.question_archetypes}
        role_ids |= await upsert(connection, t["role_template"], [row], ["slug"], key="slug")
        rows = [{"role_template_id": role_ids[role.slug], "role_template_version": role.version,
                 "skill_id": skill_ids[r.skill], "weight": r.weight, "importance": r.importance.value,
                 "required_level": r.required_level,
                 "assessment_mode": r.assessment_mode.value if r.assessment_mode else None,
                 "evaluation_notes": r.evaluation_notes} for r in role.skill_set]
        await upsert(connection, t["role_skill_set"], rows, ["role_template_id", "role_template_version", "skill_id"],
                     returning=None)
        counts["role_skill_set"] = counts.get("role_skill_set", 0) + len(rows)
    counts["role_template"] = len(role_ids)
    # ---- companies, their dated evidence, their skill rows
    for company in catalog.companies.values():
        dated = [e for e in company.evidence if e.get("observed_at")]
        row = {"slug": company.slug, "display_name": company.display_name, "industry": company.industry,
               "core_values": company.core_values, "risk_tolerance": company.risk_tolerance,
               "interview_style": company.interview_style, "company_weight_share": company.company_weight_share,
               "culture_prompt_block": company.culture_prompt_block, "is_public": company.is_public,
               "version": company.version, "evidence_count": len(company.evidence),
               "evidence_latest_at": max((date.fromisoformat(e["observed_at"]) for e in dated), default=None)}
        company_id = (await upsert(connection, t["company_profile"], [row], ["slug"], key="slug"))[company.slug]
        await connection.execute(delete(t["company_evidence"]).where(t["company_evidence"].c.company_profile_id == company_id))
        evidence_ids: dict[str, object] = {}
        for evidence in company.evidence:
            inserted = await connection.execute(insert(t["company_evidence"]).values(
                company_profile_id=company_id, source_type=evidence["source_type"],
                role_scope=evidence.get("role_scope"), seniority_scope=evidence.get("seniority_scope"),
                site=evidence.get("site"), observed_at=date.fromisoformat(evidence["observed_at"]),
                source_url=evidence.get("source_url"), summary=evidence["summary"],
                confidence=evidence["confidence"], added_by=evidence.get("added_by"),
                supports_skill_ids=[skill_ids[k] for k in evidence.get("supports_skills", [])],
                supports_style_keys=evidence.get("supports_style_keys", []),
            ).returning(t["company_evidence"].c.id))
            evidence_ids[evidence["id"]] = inserted.scalar_one()
        await connection.execute(delete(t["company_skill_set"]).where(
            (t["company_skill_set"].c.company_profile_id == company_id)
            & (t["company_skill_set"].c.company_profile_version == company.version)))
        for r in company.skill_set:
            await connection.execute(insert(t["company_skill_set"]).values(
                company_profile_id=company_id, company_profile_version=company.version,
                skill_id=skill_ids[r.skill], scope=r.scope, scope_family=r.scope_family,
                scope_role_template_id=role_ids.get(r.scope_role) if r.scope == "role" else None,
                weight=r.weight, importance=r.importance.value, required_level_offset=r.required_level_offset,
                required_level_min=r.required_level_min,
                assessment_mode=r.assessment_mode.value if r.assessment_mode else None,
                examination_notes=r.examination_notes,
                evidence_ids=[evidence_ids[e] for e in r.evidence if e in evidence_ids]))
    counts["company_profile"] = len(catalog.companies)
    # ---- tips (the database column holds the English template; other languages stay in the seed file
    #      until tips_library gains a per-language column)
    tip_rows = [{"key": tip.key, "category": tip.category, "trigger_conditions": tip.trigger_conditions,
                 "applicable_families": tip.applicable_families,
                 "applicable_skill_ids": [skill_ids[k] for k in tip.applicable_skills],
                 "improves_skill_ids": [skill_ids[k] for k in tip.improves_skills],
                 "tip_template": tip.templates["en"], "example_before": tip.example_before,
                 "example_after": tip.example_after, "delivery_timing": tip.delivery_timing,
                 "severity": tip.severity, "origin": "curated", "is_active": tip.is_active}
                for tip in catalog.tips.values()]
    tip_ids = await upsert(connection, t["tips_library"], tip_rows, ["key"], key="key")
    counts["tips_library"] = len(tip_rows)
    # ---- questions: base row (English as the canonical text), skills, translations
    # Review metadata (status, reviewer, parity) belongs to a content revision. A re-import with the
    # same content keeps it; changed content sends the question back to review, and says so.
    ordered = sorted(catalog.questions.values(), key=lambda q: q.variation_of is not None)
    question_ids: dict[str, object] = {}
    existing_rows = {
        r.key: r for r in (await connection.execute(select(
            t["question"].c.id, t["question"].c.key, t["question"].c.status, t["question"].c.reviewed_by,
            t["question"].c.assets))).all()}
    existing_parity = {
        (r.question_id, r.language): r for r in (await connection.execute(select(
            t["question_translation"].c.question_id, t["question_translation"].c.language,
            t["question_translation"].c.parity_checked))).all()}
    for question in ordered:
        english = question.text("en")
        new_hash = content_hash(question)
        existing = existing_rows.get(question.key)
        preserve_review = False
        if existing is not None:
            old_hash = (existing.assets or {}).get("content_hash")
            if old_hash == new_hash:
                preserve_review = True
                REPORT.append(f"unchanged: {question.key} (review metadata kept: {existing.status})")
            elif existing.status == "published" or existing.reviewed_by:
                REPORT.append(f"REVIEW RESET: {question.key} was {existing.status} (reviewed by {existing.reviewed_by}); "
                              f"content changed, now in_review")
            else:
                REPORT.append(f"updated: {question.key}")
        else:
            REPORT.append(f"new: {question.key}")
        row = {
            "key": question.key, "status": question.status, "origin": question.origin,
            "variation_of_id": question_ids.get(question.variation_of), "format": question.format,
            "practice_modes": question.practice_modes, "subject_id": skill_ids[question.subject],
            "difficulty": question.difficulty, "estimated_minutes": question.estimated_minutes,
            "requirements": english.requirements, "accepted_approaches": english.accepted_approaches,
            "reference_solution": english.reference_solution,
            "hints": list(english.hints),          # plain strings, level 1 to 3; the format the web app renders
            "common_errors": [{"key": e.key, "core": e.core, "skill": e.skill,
                               "tip_id": str(tip_ids[e.tip_key]) if e.tip_key else None,
                               "explanation": english.common_errors.get(e.key)} for e in question.common_errors],
            "rubric": {"criteria": [c.model_dump() for c in question.rubric]},
            "deterministic_check": question.deterministic_check,
            "choices": ({"options": english.choices, "correct_index": question.correct_choice,
                         "misconceptions": question.choice_misconceptions} if english.choices else None),
            "assets": {**question.assets, "archetype": question.archetype.value, "content_hash": new_hash},
            "source_name": question.source_name, "source_url": question.source_url, "license": question.license,
            "reuse_status": question.reuse_status, "attribution_text": question.attribution_text,
            "reviewed_by": question.reviewed_by,
            "reviewed_at": datetime.fromisoformat(question.reviewed_at) if question.reviewed_at else None,
            "review_notes": question.review_notes, "exposure_risk": question.exposure_risk,
            "version": question.version,
        }
        if preserve_review:
            for column in REVIEW_COLUMNS:
                row.pop(column, None)
        elif existing is not None:
            row["status"] = "in_review"           # changed content is never published by a script
            row["reviewed_by"], row["reviewed_at"] = None, None
        question_ids |= await upsert(connection, t["question"], [row], ["key"], key="key")
        question_id = question_ids[question.key]
        await connection.execute(delete(t["question_skill"]).where(t["question_skill"].c.question_id == question_id))
        for link in question.skills:
            await connection.execute(insert(t["question_skill"]).values(
                question_id=question_id, skill_id=skill_ids[link.skill], weight=link.weight, is_primary=link.primary))
        for language, text in question.translations.items():
            translation = {
                "question_id": question_id, "language": language, "prompt": text.prompt,
                "requirements": text.requirements, "hints": list(text.hints),
                "reference_solution": text.reference_solution, "choices": text.choices,
                "common_errors": text.common_errors, "parity_checked": text.parity_checked,
                "parity_checked_by": text.parity_checked_by,
                "parity_checked_at": datetime.now().astimezone() if text.parity_checked else None,
            }
            if preserve_review and (question_id, language) in existing_parity:
                for column in ("parity_checked", "parity_checked_by", "parity_checked_at"):
                    translation.pop(column)
            await upsert(connection, t["question_translation"], [translation], ["question_id", "language"], returning=None)
    counts["question"] = len(question_ids)
    glossary = [{"key": g["key"], "he": g["he"], "en": g["en"], "keep_english": g.get("keep_english", False),
                 "notes": g.get("notes")} for g in catalog.glossary]
    await upsert(connection, t["term_glossary"], glossary, ["key"], returning=None)
    counts["term_glossary"] = len(glossary)
    return counts


def summarize(catalog: Catalog) -> None:
    print(f"  subjects   {len(catalog.domains)}")
    print(f"  skills     {len(catalog.leaf_skills)}")
    for role in catalog.roles.values():
        total = sum(r.weight for r in role.skill_set)
        print(f"  role       {role.slug}: {len(role.skill_set)} skills, weights sum to {total:.3f}, "
              f"seniorities {', '.join(role.seniority_profiles)}")
    print(f"  companies  {', '.join(catalog.companies)}")
    by_status: dict[str, int] = {}
    for question in catalog.questions.values():
        by_status[question.status] = by_status.get(question.status, 0) + 1
    print(f"  questions  {len(catalog.questions)} ({', '.join(f'{v} {k}' for k, v in by_status.items())})")
    print(f"  tips       {len(catalog.tips)}")
    print(f"  glossary   {len(catalog.glossary)} terms")


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="validate the seed files and stop")
    parser.add_argument("--dry-run", action="store_true",
                        help="run the whole load inside a transaction, print what would change, then roll back")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    seeds_dir = get_settings().seeds_dir
    try:
        catalog = load_catalog(seeds_dir)
    except CatalogError as exc:
        print(exc)
        return 2
    print(f"Seed files in {seeds_dir} are valid:")
    summarize(catalog)
    if args.check:
        return 0

    counts = await seed(catalog, dry_run=args.dry_run)
    await db.dispose()
    print("Question review report:")
    for line in REPORT:
        print("  " + line)
    print("Rolled back (dry run). Nothing was written." if args.dry_run else "Loaded into the database:")
    for name, count in counts.items():
        print(f"  {name:20} {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
