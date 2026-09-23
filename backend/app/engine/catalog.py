"""The content catalog: skills, roles, companies, questions, tips, glossary.

Loaded from the JSON seed files under backend/seeds/ (Data_Models §12) and
validated as a whole, so a typo in a skill key fails loudly at load time instead
of silently dropping a skill from someone's interview.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from app.engine import checks
from app.schemas.bank import LANGUAGES, BankQuestion, JobType, Tip
from app.schemas.engine import CatalogSkill, CompanySkillRow, RoleSkillRow

SENIORITIES = ("student", "junior", "mid", "senior", "staff", "principal")


class SeniorityProfile(BaseModel):
    baseline_difficulty: int = Field(ge=1, le=10)
    difficulty_ceiling: int = Field(ge=1, le=10)


class RoleSeed(BaseModel):
    slug: str
    title: str
    family: str
    sub_family: str
    description: str = ""
    seniority_profiles: dict[str, SeniorityProfile]
    question_archetypes: dict[str, float] = Field(default_factory=dict)
    skill_set: list[RoleSkillRow]
    version: int = 1


class CompanySeed(BaseModel):
    slug: str
    display_name: str
    industry: str | None = None
    core_values: list = Field(default_factory=list)
    risk_tolerance: int | None = Field(default=None, ge=1, le=10)
    interview_style: dict = Field(default_factory=dict)
    company_weight_share: float = Field(default=0.30, ge=0, le=1)
    culture_prompt_block: str = ""
    is_public: bool = True
    skill_set: list[CompanySkillRow] = Field(default_factory=list)
    evidence: list[dict] = Field(default_factory=list)
    version: int = 1


@dataclass
class Catalog:
    skills: dict[str, CatalogSkill] = field(default_factory=dict)
    roles: dict[str, RoleSeed] = field(default_factory=dict)
    companies: dict[str, CompanySeed] = field(default_factory=dict)
    questions: dict[str, BankQuestion] = field(default_factory=dict)
    tips: dict[str, Tip] = field(default_factory=dict)
    glossary: list[dict] = field(default_factory=list)
    job_types: dict[str, JobType] = field(default_factory=dict)

    @property
    def leaf_skills(self) -> dict[str, CatalogSkill]:
        return {k: s for k, s in self.skills.items() if s.node_type == "skill"}

    @property
    def domains(self) -> dict[str, CatalogSkill]:
        return {k: s for k, s in self.skills.items() if s.node_type == "domain"}

    def skill_labels(self) -> dict[str, str]:
        return {k: s.label for k, s in self.skills.items()}


class CatalogError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__(f"{len(problems)} problem(s) in the seed files:\n  - " + "\n  - ".join(problems))
        self.problems = problems


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_catalog(seeds_dir: Path, *, strict: bool = True) -> Catalog:
    """Read every seed file and validate the whole. Raises CatalogError listing every problem found."""
    seeds_dir = Path(seeds_dir)
    catalog, problems = Catalog(), []

    def parse(model, data, where):
        try:
            return model.model_validate(data)
        except (ValidationError, ValueError) as exc:
            detail = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()) \
                if isinstance(exc, ValidationError) else str(exc)
            problems.append(f"{where}: {detail}")
            return None

    for path in sorted((seeds_dir / "skills").glob("*.json")):
        for raw in _load_json(path):
            data = dict(raw)
            if "difficulty" in data:
                data["min_difficulty"], data["max_difficulty"] = data.pop("difficulty")
            data["subject"] = data.pop("parent", data.get("subject"))
            skill = parse(CatalogSkill, data, f"{path.name}:{raw.get('key')}")
            if skill:
                if skill.key in catalog.skills:
                    problems.append(f"{path.name}: duplicate skill key {skill.key!r}")
                catalog.skills[skill.key] = skill

    for path in sorted((seeds_dir / "roles").glob("*.json")):
        role = parse(RoleSeed, _load_json(path), path.name)
        if role:
            catalog.roles[role.slug] = role
    for path in sorted((seeds_dir / "companies").glob("*.json")):
        company = parse(CompanySeed, _load_json(path), path.name)
        if company:
            catalog.companies[company.slug] = company
    for path in sorted((seeds_dir / "questions").glob("*.json")):
        raw = _load_json(path)
        for item in raw if isinstance(raw, list) else [raw]:
            question = parse(BankQuestion, item, f"{path.name}:{item.get('key')}")
            if question:
                if question.key in catalog.questions:
                    problems.append(f"{path.name}: duplicate question key {question.key!r}")
                catalog.questions[question.key] = question
    tips_path = seeds_dir / "tips.json"
    if tips_path.exists():
        for item in _load_json(tips_path):
            tip = parse(Tip, item, f"tips.json:{item.get('key')}")
            if tip:
                catalog.tips[tip.key] = tip
    glossary_path = seeds_dir / "glossary.json"
    if glossary_path.exists():
        catalog.glossary = _load_json(glossary_path)
    job_types_path = seeds_dir / "job_types.json"
    if job_types_path.exists():
        for item in _load_json(job_types_path):
            job = parse(JobType, item, f"job_types.json:{item.get('key')}")
            if job:
                if job.key in catalog.job_types:
                    problems.append(f"job_types.json: duplicate job type {job.key!r}")
                for skill_key, value in job.emphasis.items():
                    if skill_key not in catalog.skills:
                        problems.append(f"job_types.json:{job.key}: unknown skill {skill_key!r}")
                    if not 0.2 <= value <= 2.5:
                        problems.append(f"job_types.json:{job.key}: emphasis for {skill_key} out of range ({value})")
                catalog.job_types[job.key] = job

    problems.extend(validate(catalog))
    if problems and strict:
        raise CatalogError(problems)
    return catalog


def validate(catalog: Catalog) -> list[str]:
    problems: list[str] = []
    leaf, domains = catalog.leaf_skills, catalog.domains

    for skill in catalog.skills.values():
        if skill.node_type == "skill":
            if skill.subject not in domains:
                problems.append(f"skill {skill.key}: parent {skill.subject!r} is not a domain")
            if set(skill.proficiency_rubric) != {"1", "2", "3", "4", "5"}:
                problems.append(f"skill {skill.key}: proficiency_rubric needs levels 1 to 5")
            if not 1 <= skill.min_difficulty <= skill.max_difficulty <= 10:
                problems.append(f"skill {skill.key}: difficulty range must sit within 1..10")
            for prerequisite in skill.prerequisites:
                if prerequisite not in leaf:
                    problems.append(f"skill {skill.key}: prerequisite {prerequisite!r} is not a leaf skill")
        elif skill.subject is not None:
            problems.append(f"domain {skill.key}: a domain has no parent")
    problems.extend(_prerequisite_cycles(leaf))

    for role in catalog.roles.values():
        total = sum(row.weight for row in role.skill_set)
        if abs(total - 1.0) > 0.005:
            problems.append(f"role {role.slug}: weights sum to {total:.4f}, expected 1.0")
        seen = set()
        for row in role.skill_set:
            if row.skill not in leaf:
                problems.append(f"role {role.slug}: {row.skill!r} is not a leaf skill in the catalog")
            if row.skill in seen:
                problems.append(f"role {role.slug}: {row.skill!r} listed twice")
            seen.add(row.skill)
            for seniority, level in row.required_level.items():
                if seniority not in SENIORITIES or not 1 <= level <= 5:
                    problems.append(f"role {role.slug}/{row.skill}: bad required level {seniority}={level}")
            missing = set(role.seniority_profiles) - set(row.required_level)
            if missing:
                problems.append(f"role {role.slug}/{row.skill}: no required level for {sorted(missing)}")
        for seniority, profile in role.seniority_profiles.items():
            if seniority not in SENIORITIES:
                problems.append(f"role {role.slug}: unknown seniority {seniority!r}")
            if profile.baseline_difficulty > profile.difficulty_ceiling:
                problems.append(f"role {role.slug}/{seniority}: baseline above ceiling")

    for company in catalog.companies.values():
        evidence_ids = {e.get("id") for e in company.evidence}
        for row in company.skill_set:
            if row.skill not in leaf:
                problems.append(f"company {company.slug}: {row.skill!r} is not a leaf skill in the catalog")
            if row.scope == "role" and row.scope_role not in catalog.roles:
                problems.append(f"company {company.slug}/{row.skill}: unknown role {row.scope_role!r}")
            # every company claim traces to a dated evidence record (Data_Models §16)
            if not row.evidence:
                problems.append(f"company {company.slug}/{row.skill}: cites no evidence record")
            for evidence_id in row.evidence:
                if evidence_id not in evidence_ids:
                    problems.append(f"company {company.slug}/{row.skill}: unknown evidence id {evidence_id!r}")
            cited = [e for e in company.evidence if e.get("id") in row.evidence]
            if row.importance.value == "core" and cited and all(e.get("source_type") == "candidate_report" for e in cited) \
                    and len(cited) < 2:
                problems.append(f"company {company.slug}/{row.skill}: a single candidate report never makes a skill core")
        for evidence in company.evidence:
            for required in ("id", "source_type", "observed_at", "summary", "confidence"):
                if not evidence.get(required):
                    problems.append(f"company {company.slug}: evidence record is missing {required!r}")

    for question in catalog.questions.values():
        if question.subject not in domains:
            problems.append(f"question {question.key}: subject {question.subject!r} is not a domain")
        for link in question.skills:
            if link.skill not in leaf:
                problems.append(f"question {question.key}: {link.skill!r} is not a leaf skill")
        primary = leaf.get(question.primary_skill)
        if primary and primary.subject != question.subject:
            problems.append(f"question {question.key}: primary skill belongs to {primary.subject!r}, not {question.subject!r}")
        for error in question.common_errors:
            if error.tip_key and error.tip_key not in catalog.tips:
                problems.append(f"question {question.key}: unknown tip {error.tip_key!r}")
        if question.variation_of and question.variation_of not in catalog.questions:
            problems.append(f"question {question.key}: variation_of {question.variation_of!r} does not exist")
        problems.extend(_self_test(question))

    for tip in catalog.tips.values():
        for key in (*tip.applicable_skills, *tip.improves_skills):
            if key not in leaf:
                problems.append(f"tip {tip.key}: {key!r} is not a leaf skill")
        if "en" not in tip.templates:
            problems.append(f"tip {tip.key}: an English template is required")
    return problems


def _prerequisite_cycles(leaf: dict[str, CatalogSkill]) -> list[str]:
    state: dict[str, int] = {}
    found: list[str] = []

    def visit(key: str, trail: list[str]) -> None:
        if state.get(key) == 2 or key not in leaf:
            return
        if state.get(key) == 1:
            found.append("prerequisite cycle: " + " -> ".join([*trail[trail.index(key):], key]))
            return
        state[key] = 1
        for prerequisite in leaf[key].prerequisites:
            visit(prerequisite, [*trail, key])
        state[key] = 2

    for key in leaf:
        visit(key, [])
    return found


def _self_test(question: BankQuestion) -> list[str]:
    """A deterministic check must accept its own known-good answers and reject its known-bad ones."""
    if not question.deterministic_check:
        return []
    problems = []
    try:
        reference = checks.run_check(question.deterministic_check, "0", sandbox=False)
        if reference is None:
            return [f"question {question.key}: deterministic_check has no type"]
    except (ValueError, KeyError, checks.BooleanParseError) as exc:
        return [f"question {question.key}: deterministic_check spec is invalid: {exc}"]
    tests = question.check_self_test or {}
    if question.deterministic_check.get("type") != "sim" and not tests.get("pass"):
        problems.append(f"question {question.key}: check_self_test needs at least one passing answer")
    for expected, answers in ((True, tests.get("pass", [])), (False, tests.get("fail", []))):
        for answer in answers:
            result = checks.run_check(question.deterministic_check, answer, sandbox=False)   # our own answers
            if result.passed is not expected:
                problems.append(f"question {question.key}: self-test answer {answer!r} gave {result.passed}, expected {expected}")
    return problems


def languages_missing(question: BankQuestion) -> list[str]:
    return [language for language in LANGUAGES if language not in question.translations]
