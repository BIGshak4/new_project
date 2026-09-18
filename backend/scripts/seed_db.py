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


async def upsert(connection, table, rows: list[dict], conflict: list[str], *, returning: str | None = "id",
                 key: str | None = None) -> dict:
    """Insert or update by `conflict` columns. Returns {key value: id} when `key` is given."""
    ids: dict = {}
    for row in rows:
        statement = insert(table).values(**row)
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


async def seed(catalog: Catalog) -> dict[str, int]:
    counts: dict[str, int] = {}
    t = {name: await db.table(name) for name in (
        "skill", "skill_dependency", "role_template", "role_skill_set", "company_profile", "company_evidence",
        "company_skill_set", "question", "question_skill", "question_translation", "tips_library", "term_glossary")}

    async with db.get_engine().begin() as connection:
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
        ordered = sorted(catalog.questions.values(), key=lambda q: q.variation_of is not None)
        question_ids: dict[str, object] = {}
        for question in ordered:
            english = question.text("en")
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
                "assets": {**question.assets, "archetype": question.archetype.value},
                "source_name": question.source_name, "source_url": question.source_url, "license": question.license,
                "reuse_status": question.reuse_status, "attribution_text": question.attribution_text,
                "reviewed_by": question.reviewed_by,
                "reviewed_at": datetime.fromisoformat(question.reviewed_at) if question.reviewed_at else None,
                "review_notes": question.review_notes, "exposure_risk": question.exposure_risk,
                "version": question.version,
            }
            question_ids |= await upsert(connection, t["question"], [row], ["key"], key="key")
            question_id = question_ids[question.key]

            await connection.execute(delete(t["question_skill"]).where(t["question_skill"].c.question_id == question_id))
            for link in question.skills:
                await connection.execute(insert(t["question_skill"]).values(
                    question_id=question_id, skill_id=skill_ids[link.skill], weight=link.weight, is_primary=link.primary))

            translations = [{
                "question_id": question_id, "language": language, "prompt": text.prompt,
                "requirements": text.requirements, "hints": list(text.hints),
                "reference_solution": text.reference_solution, "choices": text.choices,
                "common_errors": text.common_errors, "parity_checked": text.parity_checked,
                "parity_checked_by": text.parity_checked_by,
                "parity_checked_at": datetime.now().astimezone() if text.parity_checked else None,
            } for language, text in question.translations.items()]
            await upsert(connection, t["question_translation"], translations, ["question_id", "language"], returning=None)
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

    counts = await seed(catalog)
    await db.dispose()
    print("Loaded into the database:")
    for name, count in counts.items():
        print(f"  {name:20} {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
