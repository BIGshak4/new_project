"""One role-union rule shared by daily practice and frozen mock-interview sessions."""

from collections.abc import Mapping, Sequence

from app.schemas.bank import JobType

JobSelection = str | Sequence[str] | None


def combined_job(catalog: Mapping[str, JobType], selection: JobSelection) -> JobType | None:
    """Average role emphasis with union membership: a skill is excluded only when every selected role excludes it.

    Averaging each distinct role once avoids increasing the total weight when the user selects more roles. An empty
    selection is broad learning and retains the base role's complete skill set, just as a legacy goal without a role.
    """
    keys = (selection,) if isinstance(selection, str) else (selection or ())
    jobs = [catalog[key] for key in sorted(set(keys)) if key in catalog]
    if not jobs:
        return None
    if len(jobs) == 1:
        return jobs[0]
    skills = set().union(*(job.emphasis for job in jobs))
    return JobType(key="+".join(job.key for job in jobs),
                   label={lang: " · ".join(job.text("label", lang) for job in jobs) for lang in ("he", "en")},
                   emphasis={skill: sum(job.weight(skill) for job in jobs) / len(jobs) for skill in skills})
