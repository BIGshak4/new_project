"""The Question Generator (AI_Engine_Spec §5).

It receives an authoritative decision and words it. It never picks the skill or the
difficulty. Bank questions and bank hints need no LLM call at all; the model is
used for probes, escalations, step-backs and questions the bank cannot supply.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from pydantic import BaseModel

from app.engine import i18n
from app.engine.providers import LLMError, LLMRequest, LLMUsage, Provider
from app.schemas.bank import BankQuestion
from app.schemas.engine import Action, Archetype, CatalogSkill, Decision


class GeneratedQuestion(BaseModel):
    question_text: str
    question_archetype: Archetype = Archetype.CONCEPTUAL
    expected_answer_outline: str = ""
    rubric_focus: list[str] = []
    starter_code: str | None = None
    language: str | None = None


@dataclass
class GenerationResult:
    question: GeneratedQuestion
    source: str                                  # bank | bank_hint | generated | fallback
    usage: LLMUsage = field(default_factory=LLMUsage)
    model: str = ""
    latency_ms: int = 0
    flags: list[str] = field(default_factory=list)


FALLBACK_TEXT = {
    "en": {
        Action.HOLD: "Let's stay with this. Walk me through the part you were least sure about, step by step.",
        Action.ESCALATE: "Good. Now make it harder for yourself: which requirement would break your solution first if it changed, and how would you adapt?",
        Action.HINT: "Take another look at the question with this in mind: {hint}",
        Action.STEP_BACK: "Let's take a simpler angle. In your own words, what is the basic idea this question depends on?",
        Action.ENTER_SKILL: "Explain the main idea behind {skill}, with a small example.",
    },
    "he": {
        Action.HOLD: "נישאר עם השאלה הזו. הסבירו צעד אחר צעד את החלק שבו הייתם הכי פחות בטוחים.",
        Action.ESCALATE: "יפה. עכשיו החמירו את התנאים: איזו דרישה, אם תשתנה, תשבור ראשונה את הפתרון שלכם, ואיך תתאימו אותו?",
        Action.HINT: "הסתכלו שוב על השאלה עם הכיוון הזה: {hint}",
        Action.STEP_BACK: "ניגש מזווית פשוטה יותר. במילים שלכם, מהו הרעיון הבסיסי שהשאלה נשענת עליו?",
        Action.ENTER_SKILL: "הסבירו את הרעיון המרכזי של {skill}, עם דוגמה קטנה.",
    },
}


def from_bank(question: BankQuestion, language: str) -> GenerationResult:
    """A reviewed bank question is served as written. No model call, no drift."""
    text = question.text(language)
    body = question.prompt_with_code(language)
    if text.choices:
        body += "\n\n" + "\n".join(f"{chr(ord('A') + i)}. {choice}" for i, choice in enumerate(text.choices))
    return GenerationResult(
        GeneratedQuestion(question_text=body, question_archetype=question.archetype,
                          expected_answer_outline=text.reference_solution,
                          rubric_focus=[c.key for c in question.rubric], starter_code=question.assets.get("starter_code"),
                          language=question.assets.get("code_language")),
        source="bank")


def bank_hint(question: BankQuestion, level: int, language: str) -> str | None:
    hints = question.text(language).hints
    return hints[level - 1] if 1 <= level <= len(hints) else None


def decision_payload(decision: Decision, *, skill: CatalogSkill | None, question: BankQuestion | None,
                     language: str, hint_text: str | None, last_question: str | None,
                     last_answer_summary: str | None, company_style: dict | None = None) -> str:
    payload = {
        "practice_language": i18n.LANGUAGE_NAMES.get(language, "English"),
        "decision": {
            "action": decision.action.value, "reason_code": decision.reason_code,
            "target_skill": decision.target_skill, "target_difficulty": decision.target_difficulty,
            "target_archetype": decision.target_archetype.value, "probe_focus": decision.probe_focus,
            "hint_level": decision.hint_level or None, "hint_text": hint_text,
            "bridge": decision.bridge.value if decision.bridge else None,
            "bridge_from_skill": decision.bridge_from_skill,
            "invite_observed_skills": decision.invite_observed_skills,
        },
        "last_turn": {"question": last_question, "answer_summary": last_answer_summary},
    }
    if skill is not None:
        payload["skill"] = {"key": skill.key, "label": skill.label, "description": skill.description,
                            "proficiency_rubric": skill.proficiency_rubric}
    if question is not None:
        text = question.text(language)
        payload["bank_question"] = {"prompt": question.prompt_with_code(language), "requirements": text.requirements,
                                    "common_errors": list(text.common_errors.values())}
    if company_style:
        payload["company_style"] = company_style
    return json.dumps(payload, ensure_ascii=False, indent=1)


async def generate(provider: Provider, decision: Decision, *, language: str, skill: CatalogSkill | None = None,
                   question: BankQuestion | None = None, last_question: str | None = None,
                   last_answer_summary: str | None = None, session_block: str | None = None,
                   glossary: list[dict] | None = None, company_style: dict | None = None,
                   previous_questions: list[str] | None = None) -> GenerationResult:
    """Word the decision. Falls back to a templated question if the model call fails twice (§5.5)."""
    hint_text = bank_hint(question, decision.hint_level, language) if question and decision.deliver_hint else None
    system = [i18n.stable_system_block("generator", language, glossary)]
    if session_block:
        system.append(session_block)
    request = LLMRequest(
        role="generator", system=system, schema=GeneratedQuestion, prompt_version=i18n.prompt_version("generator"),
        user=decision_payload(decision, skill=skill, question=question, language=language, hint_text=hint_text,
                              last_question=last_question, last_answer_summary=last_answer_summary,
                              company_style=company_style),
    )
    flags: list[str] = []
    for _attempt in range(2):
        try:
            response = await provider.complete(request)
        except LLMError as exc:
            flags.append("generation_error_retryable" if exc.retryable else "generation_error")
            if not exc.retryable:
                break
            continue
        generated: GeneratedQuestion = response.parsed
        if previous_questions and _near_duplicate(generated.question_text, previous_questions):
            flags.append("near_duplicate_regenerated")
            request.user += "\n\nThe question you wrote repeats an earlier one in this session. Ask about a different aspect."
            continue
        return GenerationResult(generated, source="generated", usage=response.usage, model=response.model,
                                latency_ms=response.latency_ms, flags=flags)

    template = FALLBACK_TEXT.get(language, FALLBACK_TEXT["en"]).get(decision.action, FALLBACK_TEXT["en"][Action.HOLD])
    text = template.format(hint=hint_text or "", skill=skill.label if skill else decision.target_skill or "")
    return GenerationResult(GeneratedQuestion(question_text=text, question_archetype=decision.target_archetype),
                            source="fallback", flags=[*flags, "fallback_question"])


def _near_duplicate(candidate: str, previous: list[str], threshold: float = 0.8) -> bool:
    """Word-overlap check, enough to catch the model re-asking the same thing (§5.5)."""
    words = set(candidate.lower().split())
    if len(words) < 4:
        return False
    for earlier in previous:
        other = set(earlier.lower().split())
        if other and len(words & other) / len(words | other) >= threshold:
            return True
    return False
