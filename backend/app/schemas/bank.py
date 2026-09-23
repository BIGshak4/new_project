"""Question bank and tips, as authored in seed files and as loaded from the database.

The seed format is a superset of Harel's `example_question/questions.json`: same
bilingual prompt, hint and reference solution, plus what the engine needs to
evaluate an answer: catalog skills, a weighted rubric, three hint levels, named
common errors, accepted approaches and an optional deterministic check.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.schemas.engine import Archetype

LANGUAGES = ("en", "he")


class QuestionText(BaseModel):
    """Everything language-specific about a question (Data_Models §13.3)."""

    title: str = ""
    prompt: str
    requirements: str
    reference_solution: str
    hints: list[str] = Field(default_factory=list)              # level 1, 2, 3 in order
    common_errors: dict[str, str] = Field(default_factory=dict)  # error key -> explanation
    accepted_approaches: list[str] = Field(default_factory=list)
    choices: list[str] | None = None
    parity_checked: bool = False
    parity_checked_by: str | None = None


class RubricCriterion(BaseModel):
    key: str
    weight: float = Field(gt=0, le=1)
    description: dict[str, str]                                  # language -> text


class CommonError(BaseModel):
    key: str
    core: bool = False                 # a core-concept misconception makes the answer WEAK and caps the level at 2
    skill: str | None = None           # the skill this error undermines
    tip_key: str | None = None


class QuestionSkillLink(BaseModel):
    skill: str
    weight: float = Field(gt=0, le=1)
    primary: bool = False


class BankQuestion(BaseModel):
    key: str
    version: int = 1
    status: str = "in_review"
    origin: str = "original"
    variation_of: str | None = None
    format: str
    practice_modes: list[str]
    subject: str
    difficulty: int = Field(ge=1, le=10)
    estimated_minutes: int | None = None
    archetype: Archetype = Archetype.CONCEPTUAL
    skills: list[QuestionSkillLink]
    rubric: list[RubricCriterion]
    common_errors: list[CommonError] = Field(default_factory=list)
    deterministic_check: dict | None = None
    check_self_test: dict | None = None        # {"pass": [...answers], "fail": [...answers]} validated by the seed loader
    correct_choice: int | None = None
    choice_misconceptions: list[str | None] | None = None
    assets: dict = Field(default_factory=dict)
    source_name: str | None = None
    source_url: str | None = None
    license: str | None = None
    reuse_status: str = "pending_review"
    attribution_text: str | None = None
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    review_notes: str | None = None
    exposure_risk: str = "low"
    times_served: int = 0
    translations: dict[str, QuestionText]

    @model_validator(mode="after")
    def _check_shape(self) -> BankQuestion:
        problems = []
        if abs(sum(c.weight for c in self.rubric) - 1.0) > 0.01:
            problems.append("rubric weights must sum to 1.0")
        if abs(sum(s.weight for s in self.skills) - 1.0) > 0.01:
            problems.append("skill weights must sum to 1.0")
        if sum(1 for s in self.skills if s.primary) != 1:
            problems.append("exactly one primary skill is required")
        if not self.translations:
            problems.append("at least one translation is required")
        error_keys = {e.key for e in self.common_errors}
        for language, text in self.translations.items():
            if language not in LANGUAGES:
                problems.append(f"unknown language {language!r}")
            if len(text.hints) != 3:
                problems.append(f"{language}: exactly three hints (levels 1 to 3) are required")
            missing = error_keys - set(text.common_errors)
            if missing:
                problems.append(f"{language}: no explanation for common errors {sorted(missing)}")
            for criterion in self.rubric:
                if language not in criterion.description:
                    problems.append(f"{language}: rubric criterion {criterion.key!r} has no description")
        if self.format == "multiple_choice" and self.correct_choice is None:
            problems.append("multiple_choice needs correct_choice")
        if self.status == "published":
            if self.reuse_status not in ("permitted", "attribution_required"):
                problems.append("a published question needs permitted reuse")
            if not self.reviewed_by:
                problems.append("a published question needs a reviewer")
        if problems:
            raise ValueError(f"question {self.key!r}: " + "; ".join(problems))
        return self

    @property
    def primary_skill(self) -> str:
        return next(s.skill for s in self.skills if s.primary)

    @property
    def core_misconception_keys(self) -> set[str]:
        return {e.key for e in self.common_errors if e.core}

    def text(self, language: str) -> QuestionText:
        """The requested language, falling back to English, then to whatever exists."""
        return self.translations.get(language) or self.translations.get("en") or next(iter(self.translations.values()))

    def languages_ready(self) -> list[str]:
        return [language for language, text in self.translations.items() if text.parity_checked]

    def prompt_with_code(self, language: str) -> str:
        """The prompt plus the shared code block, which is stored once in assets and never translated."""
        prompt = self.text(language).prompt
        code = self.assets.get("shared_code")
        if not code:
            return prompt
        return f"{prompt}\n\n```{self.assets.get('code_language') or ''}\n{code.rstrip()}\n```"


class JobType(BaseModel):
    """A kind of job a candidate interviews for (verification, FPGA, embedded ...). It does not add skills:
    it re-weights the role's skills, so the plan, the next-question suggestion and the mock interview lean
    toward what that job asks about. Skills not listed keep emphasis 1.0."""

    key: str
    label: dict[str, str]                      # language -> label
    description: dict[str, str] = Field(default_factory=dict)
    emphasis: dict[str, float] = Field(default_factory=dict)   # skill key -> multiplier (0.3 .. 2.0)

    def weight(self, skill: str) -> float:
        return self.emphasis.get(skill, 1.0)

    def text(self, field_name: str, language: str) -> str:
        values = getattr(self, field_name)
        return values.get(language) or values.get("en") or next(iter(values.values()), "")


class TipCondition(BaseModel):
    signal: str
    op: str
    value: object


class Tip(BaseModel):
    key: str
    category: str
    severity: int = Field(default=3, ge=1, le=5)
    delivery_timing: str = "both"
    trigger_conditions: dict
    applicable_families: list[str] = Field(default_factory=list)
    applicable_skills: list[str] = Field(default_factory=list)
    improves_skills: list[str] = Field(default_factory=list)
    templates: dict[str, str]                  # language -> text with {{placeholders}}
    example_before: str | None = None
    example_after: str | None = None
    effectiveness_score: float | None = None
    is_active: bool = True
