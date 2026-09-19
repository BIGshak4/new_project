"""A model stand-in for running the API without a key (LLM_PROVIDER=scripted).

It answers instantly and deterministically so the web app can be built and demoed:
the evaluation depends only on how much the candidate wrote and whether the
deterministic check passed (which is in the user message). Never used in production.
"""

from __future__ import annotations

import re

from app.engine.providers import LLMRequest, LLMResponse, LLMUsage, ScriptedProvider

_CHECK_RE = re.compile(r'<check_result[^>]*passed="(true|false)"')
_ANSWER_RE = re.compile(r"<candidate_answer>\n(.*?)\n</candidate_answer>", re.S)


def _evaluation(request: LLMRequest) -> dict:
    answer = (_ANSWER_RE.search(request.user) or [None, ""])[1]
    words = len(answer.split())
    check = _CHECK_RE.search(request.user)
    if check and check.group(1) == "false":
        correctness, depth, level = 0.25, 0.3, 2
        summary = "The automatic check found a mismatch; the core idea is not right yet."
    elif words < 12:
        correctness, depth, level = 0.55, 0.35, 2
        summary = "Too short to show the reasoning; the direction is plausible."
    else:
        correctness, depth, level = 0.85, 0.7, 4
        summary = "Correct and reasonably explained."
    return {"correctness": correctness, "depth": depth, "clarity": min(1.0, 0.4 + words / 100), "structure": 0.6,
            "tradeoff_reasoning": 0.5, "risk_awareness": 0.5, "hedging_ratio": 0.1, "rubric_level_estimate": level,
            "key_points_hit": ["states the main idea"] if correctness > 0.5 else [],
            "key_points_missed": [] if correctness > 0.8 else ["justify each step with the requirement it satisfies"],
            "misconceptions": [], "behavior_signals": ["no_structure"] if words < 12 else ["stated_assumptions"],
            "one_line_summary": summary}


def _respond_english(request: LLMRequest):
    if request.role == "evaluator":
        return _evaluation(request)
    if request.role == "generator":
        return {"question_text": "Demo follow-up: which requirement would break your solution first if it changed, and why?",
                "question_archetype": "design", "expected_answer_outline": "names one requirement and the failure mode",
                "rubric_focus": []}
    if request.role == "feedback":
        return {"what_happened": "Demo feedback: the main idea was stated.",
                "why_it_matters": "Interviewers probe the justification next.",
                "next_step": "Next time, tie each step to the requirement it satisfies.",
                "your_reasoning_vs_reference": "Compare your steps with the reference and find the first difference."}
    if request.role == "report":
        return {"summary": "Demo report."}
    return "Next time, write the requirements as a checklist before you start."


_HEBREW_DEMO = {
    "The automatic check found a mismatch; the core idea is not right yet.": "משוב הדגמה: הבדיקה האוטומטית מצאה אי־התאמה.",
    "Too short to show the reasoning; the direction is plausible.": "משוב הדגמה: נדרש פירוט נוסף של דרך הפתרון.",
    "Correct and reasonably explained.": "משוב הדגמה: התשובה כוללת פתרון והסבר.",
    "states the main idea": "הרעיון המרכזי מופיע בתשובה",
    "justify each step with the requirement it satisfies": "נמקו כל שלב והסבירו על איזו דרישה הוא עונה",
    "Demo follow-up: which requirement would break your solution first if it changed, and why?": "שאלת המשך להדגמה: שינוי באיזו דרישה יגרום לפתרון להפסיק לעבוד, ומדוע?",
    "names one requirement and the failure mode": "ציון דרישה אחת והסבר כיצד השינוי בה יגרום לכשל",
    "Demo feedback: the main idea was stated.": "משוב הדגמה: הרעיון המרכזי הוצג.",
    "Interviewers probe the justification next.": "מראיינים עשויים לבקש לנמק את הבחירה בפתרון.",
    "Next time, tie each step to the requirement it satisfies.": "בפעם הבאה, קשרו כל שלב לדרישה שהוא ממלא.",
    "Compare your steps with the reference and find the first difference.": "השוו את שלבי הפתרון שלכם לפתרון המוצע ומצאו את ההבדל הראשון.",
    "Demo report.": "דוח הדגמה.",
    "Next time, write the requirements as a checklist before you start.": "בפעם הבאה, כתבו את הדרישות כרשימת בדיקה לפני תחילת הפתרון.",
}


def _respond(request: LLMRequest):
    reply = _respond_english(request)
    # Practice language is trusted system context, never guessed from the candidate's answer.
    if not any("## שפת התרגול: עברית" in block for block in request.system):
        return reply
    def translate(value):
        if isinstance(value, str):
            return _HEBREW_DEMO.get(value, value)
        if isinstance(value, dict):
            return {key: translate(item) for key, item in value.items()}
        if isinstance(value, list):
            return [translate(item) for item in value]
        return value
    return translate(reply)


class DemoProvider(ScriptedProvider):
    name = "scripted"
    model = "demo"

    def __init__(self):
        super().__init__(_respond)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        response = await super().complete(request)
        response.usage = LLMUsage(input_tokens=len(request.user) // 4, output_tokens=len(response.text) // 4)
        return response
