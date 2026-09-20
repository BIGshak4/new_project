"""The Evaluator: one structured LLM call that scores an answer (AI_Engine_Spec §2.3).

Failure policy (MVP_Build_Guide §7.6): one retry, then give up gracefully. The
caller gets `evaluation=None` plus flags, defaults the decision to HOLD, and the
session continues. A failed LLM call never breaks a session.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from app.engine import i18n, providers
from app.engine.providers import LLMError, LLMRefusal, LLMRequest, LLMUsage, Provider
from app.schemas.bank import BankQuestion
from app.schemas.engine import CatalogSkill, CheckResult, Evaluation

SUMMARY_MAX_CHARS = 160
BEHAVIOR_SIGNALS = {
    "stated_assumptions", "asked_clarifying_question", "jumped_to_implementation", "no_structure",
    "verified_with_example", "considered_edge_cases", "ignored_edge_cases", "hedged_heavily",
    "overconfident_wrong", "answered_different_question", "incomplete_answer", "used_hint_well",
}


@dataclass
class EvaluationResult:
    evaluation: Evaluation | None
    flags: list[str] = field(default_factory=list)
    usage: LLMUsage = field(default_factory=LLMUsage)
    model: str = ""
    latency_ms: int = 0
    prompt_version: str = ""
    attempts: int = 0

    @property
    def ok(self) -> bool:
        return self.evaluation is not None


def question_block(question: BankQuestion, language: str, skill: CatalogSkill | None) -> str:
    """Everything about the question that is the same for every candidate: the second cached block."""
    text = question.text(language)
    rubric = [{"key": c.key, "weight": c.weight, "criterion": c.description.get(language) or c.description.get("en")}
              for c in question.rubric]
    errors = [{"key": e.key, "core_concept": e.core, "explanation": text.common_errors.get(e.key, "")}
              for e in question.common_errors]
    parts = [
        f"<question key=\"{question.key}\" format=\"{question.format}\" difficulty=\"{question.difficulty}\">",
        f"<prompt>\n{question.prompt_with_code(language)}\n</prompt>",
        f"<requirements>\n{text.requirements}\n</requirements>",
        f"<rubric>\n{json.dumps(rubric, ensure_ascii=False, indent=1)}\n</rubric>",
        f"<reference_solution>\n{text.reference_solution}\n</reference_solution>",
        "<accepted_approaches>\n" + ("\n".join(f"- {a}" for a in text.accepted_approaches) or "none listed") + "\n</accepted_approaches>",
        f"<common_errors>\n{json.dumps(errors, ensure_ascii=False, indent=1)}\n</common_errors>",
    ]
    if skill is not None:
        parts.append(f"<skill key=\"{skill.key}\" label=\"{skill.label}\">\n{skill.description}\n"
                     f"<proficiency_rubric>\n{json.dumps(skill.proficiency_rubric, ensure_ascii=False, indent=1)}\n"
                     "</proficiency_rubric>\n</skill>")
    parts.append("</question>")
    return "\n".join(parts)


def follow_up_block(question_text: str, expected_answer_outline: str, skill: CatalogSkill | None, difficulty: int) -> str:
    """For generated follow-ups there is no reviewed rubric; the generator's private outline stands in."""
    parts = [f"<question generated=\"true\" difficulty=\"{difficulty}\">", f"<prompt>\n{question_text}\n</prompt>",
             f"<expected_answer_outline>\n{expected_answer_outline}\n</expected_answer_outline>",
             "<rubric>none reviewed; score against the expected answer outline</rubric>", "<common_errors>[]</common_errors>"]
    if skill is not None:
        parts.append(f"<skill key=\"{skill.key}\" label=\"{skill.label}\">\n<proficiency_rubric>\n"
                     f"{json.dumps(skill.proficiency_rubric, ensure_ascii=False, indent=1)}\n</proficiency_rubric>\n</skill>")
    parts.append("</question>")
    return "\n".join(parts)


PROTOCOL_TAGS = ("candidate_answer", "candidate_circuit", "candidate_images", "check_result", "question", "rubric",
                 "reference_solution", "accepted_approaches",
                 "common_errors", "skill", "proficiency_rubric", "expected_answer_outline", "language", "difficulty",
                 "hint_level_given", "evaluation", "band", "tone", "tip", "prompt", "requirements")
_PROTOCOL_TAG_RE = re.compile(r"<(\s*/?\s*)(" + "|".join(PROTOCOL_TAGS) + r")\b", re.IGNORECASE)


def neutralize(answer: str) -> str:
    """The answer is data. It must not be able to close its own delimiter or forge any other protocol tag
    (a fake <check_result passed="true"> inside the answer must stay visibly part of the answer)."""
    cleaned = answer.replace("​", "").replace("‌", "").replace("‍", "").replace("﻿", "")
    return _PROTOCOL_TAG_RE.sub(lambda m: "‹" + m.group(1) + m.group(2), cleaned)


def user_message(*, language: str, difficulty: int, answer: str, check: CheckResult | None,
                 hint_level: int = 0, circuit: str | None = None, images: int = 0, images_missing: int = 0) -> str:
    parts = [f"<language>{i18n.LANGUAGE_NAMES.get(language, 'English')}</language>",
             f"<difficulty>{difficulty}</difficulty>"]
    if hint_level:
        parts.append(f"<hint_level_given>{hint_level}</hint_level_given>")
    if check is not None and check.passed is not None:
        parts.append(f"<check_result type=\"{check.type}\" passed=\"{str(check.passed).lower()}\">\n{check.detail}\n"
                     f"{json.dumps(check.mismatches, ensure_ascii=False) if check.mismatches else ''}\n</check_result>")
    parts.append(f"<candidate_answer>\n{neutralize(answer)}\n</candidate_answer>")
    if circuit:
        parts.append("<candidate_circuit>\nThe candidate also drew this circuit in the editor. The netlist below was "
                     "generated by the server from the drawing; the component labels are the candidate's. Judge the "
                     "drawing as part of the answer: is the logic right, complete and cleanly structured?\n"
                     f"{neutralize(circuit)}\n</candidate_circuit>")
    if images:
        parts.append(f"<candidate_images count=\"{images}\">The image(s) above are the candidate's photos or "
                     "drawings (handwritten work, schematics, tables). Read them as part of the answer. If something "
                     "is unreadable or cut off, say so in the summary and do not guess in the candidate's favour or "
                     "against them.</candidate_images>")
    if images_missing:
        parts.append(f"<candidate_images count=\"{images_missing}\" available=\"false\">The candidate attached "
                     f"{images_missing} image(s) that could not be provided to you. Judge what you can see; mention "
                     "in the summary that part of the answer was an image you did not receive.</candidate_images>")
    parts.append("Score the candidate answer against the rubric. Credit any accepted approach.")
    return "\n".join(parts)


def sanitize(evaluation: Evaluation, known_error_keys: set[str]) -> Evaluation:
    """Only known keys flow onward; the one free-text field is capped (AI_Engine_Spec §9)."""
    summary = " ".join(evaluation.one_line_summary.split())[:SUMMARY_MAX_CHARS]
    return evaluation.model_copy(update={
        "misconceptions": [m for m in evaluation.misconceptions if m in known_error_keys],
        "behavior_signals": [s for s in evaluation.behavior_signals if s in BEHAVIOR_SIGNALS],
        "key_points_hit": [p.strip()[:200] for p in evaluation.key_points_hit[:8]],
        "key_points_missed": [p.strip()[:200] for p in evaluation.key_points_missed[:8]],
        "one_line_summary": summary,
    })


async def evaluate(provider: Provider, *, question_context: str, known_error_keys: set[str], language: str,
                   difficulty: int, answer: str, check: CheckResult | None = None, hint_level: int = 0,
                   glossary: list[dict] | None = None, max_attempts: int = 2, circuit: str | None = None,
                   images: list[tuple[str, bytes]] | None = None, images_missing: int = 0) -> EvaluationResult:
    images = list(images or [])
    request = LLMRequest(
        role="evaluator",
        system=[i18n.stable_system_block("evaluator", language, glossary), question_context],
        user=user_message(language=language, difficulty=difficulty, answer=answer, check=check, hint_level=hint_level,
                          circuit=circuit, images=len(images), images_missing=images_missing),
        schema=Evaluation, prompt_version=i18n.prompt_version("evaluator"), images=images,
    )
    result = EvaluationResult(evaluation=None, prompt_version=request.prompt_version)
    if not answer.strip() and not circuit and not images:
        result.evaluation = Evaluation(correctness=0, depth=0, clarity=0, structure=0, tradeoff_reasoning=0.5,
                                       risk_awareness=0.5, hedging_ratio=0, rubric_level_estimate=1,
                                       behavior_signals=["incomplete_answer"], one_line_summary="No answer given.")
        result.flags.append("empty_answer")
        return result

    for attempt in range(1, max_attempts + 1):
        result.attempts = attempt
        try:
            response = await providers.call(provider, request)
        except LLMRefusal:
            result.flags.append("eval_refused")
            return result
        except LLMError as exc:
            result.flags.append("eval_error_retryable" if exc.retryable else "eval_error")
            if exc.retryable and attempt < max_attempts:
                continue
            result.flags.append("eval_failed")
            return result
        result.usage, result.model, result.latency_ms = response.usage, response.model, response.latency_ms
        result.evaluation = sanitize(response.parsed, known_error_keys)
        return result
    result.flags.append("eval_failed")
    return result
