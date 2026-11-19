"""The automatic check's one-line result, in the language of the attempt.

`CheckResult.detail` and the code runner's `detail` are written in English where the check runs: the judge reads
them, they are stored with the answer, and the runner is a separate service. A Hebrew attempt showed them as they
were (language verification, 2026-11-14). The stored text stays English; this module retells it when a view is
built. A sentence it does not know is returned unchanged, so a new message is never lost, only untranslated.
"""

from __future__ import annotations

import re
from collections.abc import Callable

SCOPE_MARK = "\nAutomated test scope: "
SCOPE_WORDS = {"he": "\nהיקף הבדיקה האוטומטית: "}

# the test-scope sentence of each question with code tests, English -> the other languages (seeds/execution_cases.json);
# filled by the code execution service when it loads its fixtures
_scopes: dict[str, dict[str, str]] = {}


def learn_scopes(fixtures: dict) -> None:
    for fixture in fixtures.values():
        contract = fixture.get("contract") if isinstance(fixture, dict) else None
        if isinstance(contract, dict) and contract.get("en"):
            _scopes[contract["en"]] = {k: v for k, v in contract.items() if k != "en" and v}


# what a truth-table answer that could not be read says after "could not parse the answer: "
_PARSE_HE: list[tuple[re.Pattern, str]] = [(re.compile(p), t) for p, t in [
    (r"unexpected character (?P<a>.+) at position (?P<b>\d+)", "תו לא צפוי {a} במקום {b}"),
    (r"unknown variable (?P<a>.+)", "משתנה לא מוכר {a}"),
    (r"unexpected token (?P<a>.+)", "סימן לא צפוי {a}"),
    (r"unexpected end of expression", "הביטוי נקטע באמצע"),
    (r"more than (?P<a>\d+) nested parentheses", "יותר מ-{a} רמות של סוגריים"),
    (r"missing closing parenthesis", "חסרה סגירת סוגריים"),
    (r"expression longer than (?P<a>\d+) characters", "הביטוי ארוך מ-{a} תווים"),
    (r"no Boolean expression over (?P<a>.+) was found in the answer", "לא נמצא בתשובה ביטוי בוליאני במשתנים {a}"),
    (r"invalid truth table headers", "כותרות טבלת האמת אינן תקינות"),
    (r"the input columns must match (?P<a>.+)", "עמודות הקלט צריכות להיות {a}"),
    (r"unexpected number of rows or outputs", "מספר השורות או היציאות אינו כצפוי"),
    (r"the expected output column could not be identified", "לא זוהתה עמודת המוצא המבוקשת"),
    (r"invalid truth table row", "שורה לא תקינה בטבלת האמת"),
    (r"some required output cells are empty", "חלק מתאי המוצא הנדרשים ריקים"),
    (r"table has (?P<a>\d+) rows, expected (?P<b>\d+)", "בטבלה {a} שורות, נדרשות {b}"),
    (r"no expression or table in the answer", "אין בתשובה ביטוי או טבלה"),
]]

# why the runner did nothing, after "No execution was performed: " (the messages of repo/executions.py)
_REFUSED_HE = {
    "the code execution daily allowance has been reached": "מכסת ההרצות היומית נוצלה",
    "please wait before running code again": "המתינו מעט לפני הרצה נוספת",
    "the code runner is busy; please retry shortly": "סביבת ההרצה עמוסה; נסו שוב בעוד רגע",
}


def _parse_he(match: re.Match) -> str:
    inner = match["inner"]
    for pattern, template in _PARSE_HE:
        found = pattern.fullmatch(inner)
        if found:
            return "לא הצלחנו לקרוא את התשובה: " + template.format(**found.groupdict())
    return "לא הצלחנו לקרוא את התשובה"


def _refused_he(match: re.Match) -> str:
    reason = _REFUSED_HE.get(match["inner"])
    return "הקוד לא הורץ: " + reason if reason else "הקוד לא הורץ"


_HE: list[tuple[re.Pattern, str | Callable[[re.Match], str]]] = [(re.compile(p, re.DOTALL), t) for p, t in [
    # engine/checks.py: truth table
    (r"could not parse the answer: (?P<inner>.*)", _parse_he),
    (r"matches all (?P<a>\d+) specified rows", "התשובה תואמת את כל {a} השורות שהוגדרו"),
    (r"(?P<a>\d+) of (?P<b>\d+) specified rows differ", "{a} מתוך {b} השורות שהוגדרו שונות"),
    # engine/checks.py: numeric
    (r"no value named (?P<a>.+) was found in the answer", "לא נמצא בתשובה ערך בשם {a}"),
    (r"could not read a number: .*", "לא נמצא מספר בתשובה"),
    (r"unit mismatch: expected (?P<a>.+), got (?P<b>.+)", "יחידות לא מתאימות: ציפינו ל-{a}, התקבל {b}"),
    (r"within tolerance of (?P<a>.+)", "בטווח הסטייה המותרת סביב {a}"),
    (r"expected (?P<a>.+), got (?P<b>.+)", "הערך הצפוי {a}, התקבל {b}"),
    # engine/checks.py: code and simulation
    (r"Automatic code execution is unavailable; the answer is reviewed as written\.",
     "הרצת קוד אוטומטית אינה זמינה; התשובה נבדקת כפי שנכתבה."),
    (r"simulation checks are not available yet", "בדיקות סימולציה עדיין אינן זמינות"),
    # services/code_execution.py
    (r"No verified execution result is available\. The isolated runner is temporarily unavailable\.",
     "אין תוצאת הרצה מאומתת. סביבת ההרצה המבודדת אינה זמינה כרגע."),
    (r"No execution was performed: (?P<inner>.*)", _refused_he),
    (r"No execution result arrived in time; the answer is reviewed as written\.",
     "תוצאת ההרצה לא הגיעה בזמן; התשובה נבדקת כפי שנכתבה."),
    (r"The isolated runner is unavailable; code is saved and reviewed without execution\.",
     "סביבת ההרצה אינה זמינה; הקוד נשמר ונבדק בלי הרצה."),
    # the runner itself (apps/executor/lib/runner.mjs, job.mjs)
    (r"(?:Code execution|Execution) is unavailable\.", "הרצת הקוד אינה זמינה."),
    (r"Compilation exceeded its time limit\.", "ההידור חרג ממגבלת הזמן."),
    (r"The compiler rejected the submitted code\.", "המהדר דחה את הקוד שהוגש."),
    (r"HDL elaboration exceeded its time limit\.", "בניית תכן ה-HDL (elaboration) חרגה ממגבלת הזמן."),
    (r"The HDL design could not be elaborated\.", "לא ניתן היה לבנות את תכן ה-HDL (elaboration)."),
    (r"Compilation succeeded\. No executable top or question tests were available; correctness was not assessed\.",
     "ההידור הצליח. לא היו מודול עליון להרצה או בדיקות לשאלה, ולכן הנכונות לא נבדקה."),
    (r"Test (?P<a>\d+) exceeded its time limit\.", "בדיקה {a} חרגה ממגבלת הזמן."),
    (r"Test (?P<a>\d+) did not return a serializable value\.", "בדיקה {a} לא החזירה ערך שאפשר לקרוא."),
    (r"(?P<a>\d+)/(?P<b>\d+) question tests passed\.", "{a} מתוך {b} בדיקות השאלה עברו."),
    (r"The program or simulation exceeded its time limit\.", "התוכנית או הסימולציה חרגו ממגבלת הזמן."),
    (r"The program ran successfully\. This question has no automated tests for this language; correctness was not "
     r"assessed\.", "התוכנית רצה בהצלחה. לשאלה הזו אין בדיקות אוטומטיות בשפה הזו, ולכן הנכונות לא נבדקה."),
    (r"The execution reached its total time limit\. No correctness result was inferred\.",
     "ההרצה הגיעה למגבלת הזמן הכוללת. לא נקבעה תוצאת נכונות."),
    (r"The isolated execution service could not finish .*\. Please retry later\.",
     "שירות ההרצה המבודד לא השלים את הפעולה. נסו שוב מאוחר יותר."),
]]

_SENTENCES = {"he": _HE}


def in_language(detail: str | None, language: str | None) -> str:
    """`detail` as a user of `language` reads it; unchanged in English and for a sentence this module does not know."""
    detail = detail or ""
    sentences = _SENTENCES.get(language or "en")
    if not sentences or not detail:
        return detail
    body, mark, scope = detail.partition(SCOPE_MARK)
    for pattern, told in sentences:
        match = pattern.fullmatch(body)
        if match:
            body = told(match) if callable(told) else told.format(**match.groupdict())
            break
    if not mark:
        return body
    return body + SCOPE_WORDS[language] + _scopes.get(scope, {}).get(language, scope)


def execution_in_language(execution, language: str | None):
    """A stored or fresh code-run result (a dict or an ExecutionResult) with its `detail` retold; None stays None."""
    if execution is None or language not in _SENTENCES:
        return execution
    if isinstance(execution, dict):
        return {**execution, "detail": in_language(execution.get("detail"), language)}
    return execution.model_copy(update={"detail": in_language(execution.detail, language)})
