"""One role-union rule shared by daily practice and frozen mock-interview sessions."""

from collections.abc import Mapping, Sequence

from app.schemas.bank import JobType
from app.schemas.engine import IMPORTANCE_RANK, RoleSkillRow

JobSelection = str | Sequence[str] | None


def _selected(catalog: Mapping[str, JobType], selection: JobSelection) -> list[JobType]:
    """Each distinct known job type once, in a stable order; an unknown key is ignored, never an error here."""
    keys = (selection,) if isinstance(selection, str) else (selection or ())
    return [catalog[key] for key in sorted(set(keys)) if key in catalog]


def combined_job(catalog: Mapping[str, JobType], selection: JobSelection) -> JobType | None:
    """Average role emphasis with union membership: a skill is excluded only when every selected role excludes it.

    Averaging each distinct role once avoids increasing the total weight when the user selects more roles. An empty
    selection is broad learning and retains the base role's complete skill set, just as a legacy goal without a role.
    A union carries membership, emphasis and labels only: the plan's rows, the job types' own skills included, come
    from `plan_rows`.
    """
    jobs = _selected(catalog, selection)
    if not jobs:
        return None
    if len(jobs) == 1:
        return jobs[0]
    skills = set().union(*(job.emphasis for job in jobs))
    listed = set().union(*(job.questions for job in jobs))     # a listed question belongs when any selected role has it
    return JobType(key="+".join(job.key for job in jobs),
                   label={lang: " · ".join(job.text("label", lang) for job in jobs) for lang in ("he", "en")},
                   emphasis={skill: sum(job.weight(skill) for job in jobs) / len(jobs) for skill in skills},
                   questions={key: any(job.questions.get(key, False) for job in jobs) for key in sorted(listed)})


def _rows_for(role_rows: Sequence[RoleSkillRow], job: JobType) -> list[RoleSkillRow]:
    """The role's rows as one job type sees them: its own rows replace or join the role's, emphasis multiplies every
    weight, and an excluded skill (emphasis 0) is dropped."""
    own = {row.skill: row for row in job.skills}
    in_role = {row.skill for row in role_rows}
    rows = [own.get(row.skill, row) for row in role_rows] + [row for row in job.skills if row.skill not in in_role]
    return [row.model_copy(update={"weight": row.weight * job.weight(row.skill)}) for row in rows
            if not job.excludes(row.skill)]


def plan_rows(role_rows: Sequence[RoleSkillRow], catalog: Mapping[str, JobType],
              selection: JobSelection) -> list[RoleSkillRow]:
    """The skill rows a plan is merged from, for the selected job types (the practice plan and the mock interview
    both start here).

    One job type: `_rows_for`. Several: the union of their rows, each weight averaged over the selected job types
    (a job type without the skill counts as 0, so selecting more roles spreads the weight instead of adding to it),
    with the highest importance and the highest required level any of them asks for. No job type: the role as is.
    """
    jobs = _selected(catalog, selection)
    if not jobs:
        return list(role_rows)
    per_job = [_rows_for(role_rows, job) for job in jobs]
    if len(per_job) == 1:
        return per_job[0]
    by_skill: dict[str, list[RoleSkillRow]] = {}
    for rows in per_job:
        for row in rows:
            by_skill.setdefault(row.skill, []).append(row)
    merged = []
    for rows in by_skill.values():
        lead = max(rows, key=lambda row: IMPORTANCE_RANK[row.importance])
        levels: dict[str, int] = {}
        for row in rows:
            for seniority, level in row.required_level.items():
                levels[seniority] = max(level, levels.get(seniority, level))
        merged.append(lead.model_copy(update={"weight": sum(row.weight for row in rows) / len(jobs),
                                              "required_level": levels}))
    return merged
