"""The Question Generator (AI_Engine_Spec §5).

It receives an authoritative decision and words it. It never picks the skill or the
difficulty. Bank questions and bank hints need no LLM call at all; the model is
used for probes, escalations, step-backs and questions the bank cannot supply.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from pydantic import BaseModel

from app.engine import i18n, providers
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


# what a template follow-up's answer is graded against: the hint template re-asks the question, so the missed points
# apply; the other templates ask about the candidate's own reasoning, so no particular point is required
FALLBACK_OUTLINE = {
    "en": "The candidate explains one part of their own solution to the original question, step by step, correctly "
          "and with reasoning. No particular point is required; grade the correctness and depth of the explanation.",
    "he": "המועמד מסביר חלק אחד מהפתרון שלו לשאלה המקורית, צעד אחר צעד, נכון ועם נימוק. אין נקודה מסוימת שנדרשת; "
          "יש לדרג את נכונות ההסבר ואת עומקו.",
}
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
                     last_answer_summary: str | None, company_style: dict | None = None,
                     answer_covered: list[str] | None = None, check_passed: bool | None = None) -> str:
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
        "last_turn": {"question": last_question, "answer_summary": last_answer_summary,
                      # what the answer already made: settled, never asked again (generator.v2)
                      "answer_covered": list(answer_covered or []), "check_passed": check_passed},
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
                   previous_questions: list[str] | None = None, answer_covered: list[str] | None = None,
                   check_passed: bool | None = None) -> GenerationResult:
    """Word the decision. At most two model calls: a reply that a guard rejects is asked for once more with a note;
    a reply that is flawed but usable is kept in reserve, so the template (§5.5) is the last resort only."""
    hint_text = bank_hint(question, decision.hint_level, language) if question and decision.deliver_hint else None
    system = [i18n.stable_system_block("generator", language, glossary)]
    if session_block:
        system.append(session_block)
    request = LLMRequest(
        role="generator", system=system, schema=GeneratedQuestion, prompt_version=i18n.prompt_version("generator"),
        user=decision_payload(decision, skill=skill, question=question, language=language, hint_text=hint_text,
                              last_question=last_question, last_answer_summary=last_answer_summary,
                              company_style=company_style, answer_covered=answer_covered, check_passed=check_passed),
    )
    question_values = _example_values_of(question, language, hint_text) if decision.action in EXAMPLE_GUARDED else set()
    flags: list[str] = []
    usage, latency_ms, model = LLMUsage(), 0, ""
    reserve: GeneratedQuestion | None = None            # flawed but usable: returned if the second call does no better
    reserve_lists_examples = False
    for _attempt in range(2):
        try:
            response = await providers.call(provider, request)
        except LLMError as exc:
            flags.append("generation_error_retryable" if exc.retryable else "generation_error")
            if not exc.retryable:
                break
            continue
        usage, latency_ms, model = _add_usage(usage, response.usage), latency_ms + response.latency_ms, response.model
        generated: GeneratedQuestion = response.parsed
        if hint_text and question is not None and _restates_prompt(generated.question_text, question.text(language).prompt):
            # the model pasted the question again with the hint inside (seen in Hebrew, twice): ask once more; the
            # reserve says it briefly, with the outline the model wrote for the hint
            template = FALLBACK_TEXT.get(language, FALLBACK_TEXT["en"])[Action.HINT]
            reserve = GeneratedQuestion(question_text=template.format(hint=hint_text),
                                        question_archetype=generated.question_archetype,
                                        expected_answer_outline=generated.expected_answer_outline)
            flags.append("hint_restated_prompt")
            request.user += ("\n\nThe question you wrote restates the whole original question. Give only the hint, in "
                             "one or two sentences, and invite the candidate to try again.")
            continue
        if previous_questions and _near_duplicate(generated.question_text, previous_questions):
            flags.append("near_duplicate_regenerated")
            request.user += "\n\nThe question you wrote repeats an earlier one in this session. Ask about a different aspect."
            continue
        listed = _listed_examples(generated.question_text, question_values)
        if listing_weight(listed) >= EXAMPLE_LIMIT:
            # the follow-up makes the candidate work through the question's own examples (pilot, 2026-10-03): ask once
            # more; if the second wording does it too, it is kept and flagged, never replaced by a template
            if _attempt == 1:
                flags.append("examples_listed_kept")
                return GenerationResult(generated, source="generated", usage=usage, model=model,
                                        latency_ms=latency_ms, flags=flags)
            flags.append("examples_listed_regenerated")
            reserve, reserve_lists_examples = generated, True
            request.user += ("\n\nThe question you wrote makes the candidate work through the question's own examples ("
                             + ", ".join(sorted(listed)) + "). Do not ask them to compute, trace or list given examples. "
                             + EXAMPLE_NOTE.get(decision.action, EXAMPLE_NOTE[Action.HOLD]))
            continue
        return GenerationResult(generated, source="generated", usage=usage, model=model, latency_ms=latency_ms,
                                flags=flags)

    if reserve is not None:
        if reserve_lists_examples:
            flags.append("examples_listed_kept")
        return GenerationResult(reserve, source="generated", usage=usage, model=model, latency_ms=latency_ms,
                                flags=flags)
    template = FALLBACK_TEXT.get(language, FALLBACK_TEXT["en"]).get(decision.action, FALLBACK_TEXT["en"][Action.HOLD])
    text = template.format(hint=hint_text or "", skill=skill.label if skill else decision.target_skill or "")
    return GenerationResult(GeneratedQuestion(question_text=text, question_archetype=decision.target_archetype,
                                              expected_answer_outline=fallback_outline(decision, language)),
                            source="fallback", usage=usage, model=model, latency_ms=latency_ms,
                            flags=[*flags, "fallback_question"])


def fallback_outline(decision: Decision, language: str) -> str:
    """What a template follow-up's answer is graded against (never an empty outline, review finding 2026-10-03)."""
    if decision.action == Action.HINT and decision.probe_focus:
        return decision.probe_focus
    return FALLBACK_OUTLINE.get(language, FALLBACK_OUTLINE["en"])


def _add_usage(total: LLMUsage, more: LLMUsage) -> LLMUsage:
    """Every call is metered, including a reply that was asked for again."""
    return LLMUsage(input_tokens=total.input_tokens + more.input_tokens,
                    output_tokens=total.output_tokens + more.output_tokens,
                    cache_read_tokens=total.cache_read_tokens + more.cache_read_tokens,
                    cache_write_tokens=total.cache_write_tokens + more.cache_write_tokens)


def _sentences(text: str) -> list[str]:
    """The text's sentences of 15 characters or more, whitespace normalised."""
    parts = re.split(r"(?<=[.?!:;])\s+|\n+", text)
    return [flat for flat in (" ".join(p.split()) for p in parts) if len(flat) >= 15]


def _restates_prompt(candidate: str, prompt: str) -> bool:
    """True when the generated follow-up contains most of the original prompt verbatim: its first 60 %, or 60 % of
    its sentences (a hint spliced into the middle of the restated prompt, seen on 2026-10-02)."""
    flat_prompt = " ".join(prompt.split())
    flat = " ".join(candidate.split())
    if len(flat_prompt) < 40:
        return False
    head = flat_prompt[: max(40, int(len(flat_prompt) * 0.6))]
    if head in flat:
        return True
    sentences = _sentences(prompt)
    if len(sentences) < 2:
        return False
    return sum(1 for sentence in sentences if sentence in flat) >= 0.6 * len(sentences)


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


# ----------------------------------------------------------------------------- the question's own examples

# Follow-ups that may not make the candidate work through the question's listed examples. A hint re-asks the question
# and delivers reviewed text, so it is guarded by the restated-prompt check instead.
EXAMPLE_GUARDED = {Action.HOLD, Action.ESCALATE, Action.STEP_BACK}
EXAMPLE_LIMIT = 2                 # weight of the question's example values named in one follow-up (see listing_weight)
EXAMPLE_NOTE = {                  # the second ask, worded for what the action is about
    Action.HOLD: "Ask one question about the idea behind the missed point; if one concrete case is essential, use at "
                 "most one value.",
    Action.ESCALATE: "Keep the problem grown by one step (a constraint, an edge case, a scale factor) and refer to "
                     "inputs by their role, not by the question's values.",
    Action.STEP_BACK: "Ask one plain question about the fundamental idea underneath, with no values from the question.",
}

_SIZED = r"\d+'[bBhHdD][0-9A-Fa-f_]+"
_NUM = r"-?(?:0[xX][0-9A-Fa-f]+|\d+)"
_ARRAY = re.compile(r"\[\s*" + _NUM + r"(?:\s*,\s*" + _NUM + r")+\s*\]")                 # [1,4,4]
_TUPLE = re.compile(r"\(\s*" + _NUM + r"(?:\s*,\s*" + _NUM + r")+\s*\)")                 # (250,12)
_RUN = re.compile(r"(?<![\w.,=\[(])" + _NUM + r"(?:\s*,\s*" + _NUM + r"){2,}(?![\w\])]|\.\d|\s*,\s*-?\d)")   # 2,2,1,2 in prose
_QUOTED = re.compile(r"(?<!\w)[\"'“”‘’]([^\"'“”‘’\n]{1,40})[\"'“”‘’](?!\w)")                # "([)]", '1011'
_END = r"(?![\w]|\.\d)"             # a value ends at a non-word character; a full stop ends it too, a decimal point does not
_PAIR = re.compile(r"(?<![\w'])([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(" + _SIZED + r"|0[xX][0-9A-Fa-f]+|0[bB][01_]+|\d+)(?!')" + _END)
# a value may carry one or two Hebrew prefix letters written straight onto it (ב1010, ל0101); Hebrew letters are \w, so the
# lookbehind names the characters that may not precede a value instead
_LITERAL = re.compile(r"(?<![A-Za-z0-9_.֐-׿])[בהוכלמש]{0,2}(" + _SIZED
                      + r"|0[xX][0-9A-Fa-f]+|0[bB][01_]+|[01]{3,})(?!')" + _END)
_BARE = re.compile(r"[01]{3,}|0[xX][0-9A-Fa-f]+|\d+'[bBhHdD][0-9A-Fa-f_]+|\d+")


def _canonical(value: str) -> str:
    """One form per value: bit strings as they are, hex as the bits it stands for (4'hA, 0xA and 1010 are the same
    value), sized decimals as plain digits."""
    value = value.lower().replace("_", "")
    if "'b" in value:
        return value.split("'b", 1)[1]
    if "'d" in value:
        return value.split("'d", 1)[1]
    hex_digits = value.split("'h", 1)[1] if "'h" in value else value[2:] if value.startswith("0x") else None
    if hex_digits is not None and hex_digits:
        return "".join(f"{int(d, 16):04b}" for d in hex_digits)
    return value[2:] if value.startswith("0b") else value


def example_values(text: str | None) -> set[str]:
    """The literal example values in a text, one canonical form each: arrays, tuples, runs of numbers, quoted strings,
    bit strings, hex and sized literals, and name=value pairs. `req=0101` and `0101` are the same value; a
    one-character value keeps its name (`n=0`), since a bare 0 or 1 says nothing. Signal slices such as Y[3:0] or
    M[i] are not values."""
    if not text:
        return set()
    found: set[str] = set()
    for pattern in (_ARRAY, _TUPLE, _RUN):
        for match in pattern.finditer(text):
            found.add(re.sub(r"\s+", "", match.group(0)).lower())
    for quoted in _QUOTED.findall(text):
        inner = quoted.strip()
        if _BARE.fullmatch(inner):                                           # '0101' is the value 0101
            found.add(_canonical(inner))
        elif inner and not inner.isalpha():                                  # a code-like string, not a quoted word
            found.add(f"'{inner}'")
    for name, raw in _PAIR.findall(text):
        value = _canonical(raw)
        found.add(value if len(value) >= 2 else f"{name.lower()}={value}")
    for raw in _LITERAL.findall(text):
        found.add(_canonical(raw))
    return found


def listing_weight(values: set[str]) -> float:
    """How much a follow-up makes the candidate work through examples: a value counts 1; a one-bit condition such as
    `en=0` counts half, since two conditions alone describe a situation (a conceptual probe) while a value plus two
    conditions is a worked case (review finding, 2026-10-03)."""
    return sum(0.5 if "=" in v and len(v.split("=", 1)[1]) == 1 else 1.0 for v in values)


def _example_values_of(question: BankQuestion | None, language: str, hint_text: str | None) -> set[str]:
    """The bank question's example values: those in its prompt (not the shared code, whose initialisers are not
    examples) and its requirements, less any the delivered hint itself names."""
    if question is None:
        return set()
    text = question.text(language)
    values = example_values(f"{text.prompt}\n{text.requirements or ''}")
    return values - example_values(hint_text)


def _listed_examples(candidate: str, values: set[str]) -> set[str]:
    return example_values(candidate) & values if values else set()
