"""The deep-practice feedback card (AI_Engine_Spec §6.6).

Four fixed parts: what happened, why it matters, what to practice next, your
reasoning versus the reference. The model writes it from the evaluation; if that
call fails, a plain card is built from the evaluation alone so the user always
gets feedback.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from pydantic import BaseModel

from app.engine import i18n, providers
from app.engine.evaluator import neutralize
from app.engine.providers import LLMError, LLMRequest, LLMUsage, Provider
from app.schemas.bank import BankQuestion
from app.schemas.engine import Band, CheckResult, Evaluation


class FeedbackCard(BaseModel):
    what_happened: str
    why_it_matters: str
    next_step: str
    your_reasoning_vs_reference: str


@dataclass
class FeedbackResult:
    card: FeedbackCard
    source: str                                     # generated | fallback
    usage: LLMUsage = field(default_factory=LLMUsage)
    model: str = ""
    latency_ms: int = 0


_TEXT = {
    "en": {
        "hit": "You covered: {points}.", "missed": "Still missing: {points}.",
        "check_pass": "The automatic check passed: {detail}.", "check_fail": "The automatic check found a problem: {detail}.",
        "nothing": "There was not enough in the answer to evaluate.",
        "why_error": "The gap underneath: {explanation}",
        "why_strong": "This shows you can rely on this idea in a new problem.",
        "why_partial": "The core idea is there; the missing points are what interviewers probe next.",
        "why_weak": "The core idea of this question is not solid yet, so later questions built on it will be shaky too.",
        "next": "Next time, try to address this first: {point}.",
        "next_default": "Next time, try writing the requirements as a checklist before you start, and tick them off at the end.",
        "compare": "Compare your answer with the reference solution step by step and find the first place they differ.",
    },
    "he": {
        "hit": "כיסיתם: {points}.", "missed": "עדיין חסר: {points}.",
        "check_pass": "הבדיקה האוטומטית עברה: {detail}.", "check_fail": "הבדיקה האוטומטית מצאה בעיה: {detail}.",
        "nothing": "לא היה בתשובה מספיק כדי להעריך אותה.",
        "why_error": "הפער שמתחת: {explanation}",
        "why_strong": "זה מראה שאפשר לסמוך על הרעיון הזה גם בבעיה חדשה.",
        "why_partial": "הרעיון המרכזי קיים; הנקודות החסרות הן בדיוק מה שמראיינים בודקים בהמשך.",
        "why_weak": "הרעיון המרכזי של השאלה עדיין לא יציב, ולכן גם שאלות שנשענות עליו יהיו קשות.",
        "next": "בפעם הבאה, נסו לטפל קודם בנקודה הזו: {point}.",
        "next_default": "בפעם הבאה, נסו לכתוב את הדרישות כרשימת בדיקה לפני שמתחילים, ולסמן אותן בסוף.",
        "compare": "השוו את התשובה שלכם לפתרון המוצע צעד אחר צעד ומצאו את המקום הראשון שבו הם נפרדים.",
    },
}


def fallback_card(question: BankQuestion, evaluation: Evaluation, band: Band, check: CheckResult | None,
                  language: str) -> FeedbackCard:
    t = _TEXT.get(language, _TEXT["en"])
    text = question.text(language)
    happened = []
    if check is not None and check.passed is not None:
        happened.append(t["check_pass" if check.passed else "check_fail"].format(detail=check.detail))
    if evaluation.key_points_hit:
        happened.append(t["hit"].format(points="; ".join(evaluation.key_points_hit[:3])))
    if evaluation.key_points_missed:
        happened.append(t["missed"].format(points="; ".join(evaluation.key_points_missed[:3])))
    explanations = [text.common_errors[m] for m in evaluation.misconceptions if m in text.common_errors]
    if explanations:
        why = t["why_error"].format(explanation=explanations[0])
    else:
        why = t[{"STRONG": "why_strong", "PARTIAL": "why_partial", "WEAK": "why_weak"}[band.value]]
    next_step = (t["next"].format(point=evaluation.key_points_missed[0]) if evaluation.key_points_missed
                 else t["next_default"])
    return FeedbackCard(what_happened=" ".join(happened) or t["nothing"], why_it_matters=why,
                        next_step=next_step, your_reasoning_vs_reference=t["compare"])


async def build_card(provider: Provider | None, *, question: BankQuestion, evaluation: Evaluation, band: Band,
                     answer: str, check: CheckResult | None, language: str, skill_label: str | None = None,
                     glossary: list[dict] | None = None) -> FeedbackResult:
    plain = fallback_card(question, evaluation, band, check, language)
    if provider is None:
        return FeedbackResult(plain, source="fallback")
    text = question.text(language)
    context = "\n".join([
        f"<question key=\"{question.key}\">", f"<prompt>\n{question.prompt_with_code(language)}\n</prompt>",
        f"<reference_solution>\n{text.reference_solution}\n</reference_solution>",
        "<accepted_approaches>\n" + ("\n".join(f"- {a}" for a in text.accepted_approaches) or "none listed") + "\n</accepted_approaches>",
        f"<common_errors>\n{json.dumps(text.common_errors, ensure_ascii=False, indent=1)}\n</common_errors>", "</question>",
    ])
    user = "\n".join([
        f"<language>{i18n.LANGUAGE_NAMES.get(language, 'English')}</language>",
        f"<skill>{skill_label or question.primary_skill}</skill>", f"<band>{band.value}</band>",
        f"<evaluation>\n{evaluation.model_dump_json(include={'key_points_hit', 'key_points_missed', 'misconceptions', 'behavior_signals', 'one_line_summary'}, indent=1)}\n</evaluation>",
        (f"<check_result passed=\"{str(check.passed).lower()}\">{check.detail} "
         f"{json.dumps(check.mismatches, ensure_ascii=False) if check.mismatches else ''}</check_result>"
         if check is not None and check.passed is not None else ""),
        f"<candidate_answer>\n{neutralize(answer)}\n</candidate_answer>",
    ])
    request = LLMRequest(role="feedback", system=[i18n.stable_system_block("feedback", language, glossary), context],
                         user=user, schema=FeedbackCard, prompt_version=i18n.prompt_version("feedback"))
    try:
        response = await providers.call(provider, request)
    except LLMError:
        return FeedbackResult(plain, source="fallback")
    return FeedbackResult(response.parsed, source="generated", usage=response.usage, model=response.model,
                          latency_ms=response.latency_ms)
