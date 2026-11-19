"""The four backend items of the language verification (2026-11-14), fixed 2026-11-19 (Shaked: "fix the backend").

1. Skill and subject names exist in Hebrew and reach every view that names a skill.
2. Every `usage_limit` error says which limit it was, in `error.reason`.
3. The automatic check's sentence and the code runner's are told in the attempt's language; what is stored stays
   English (the judge reads it).
4. A saved plan's reasons follow the language of the request, not of the day's first build; the plain interview
   report has no English words left in Hebrew.

In-memory store, scripted model.
"""

from __future__ import annotations

import ast
import re
import uuid
from datetime import timedelta
from pathlib import Path

import pytest

from app.api import errors
from app.api.errors import ApiError
from app.engine import check_text, checks, next_question, plan_router, reporter
from app.engine.catalog import load_catalog
from app.engine.plan_router import Activity
from app.schemas.bank import LANGUAGES
from app.services.code_execution import CodeExecutionService
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.test_interview_service import Clock, interviewer, run_to_the_end
from tests.test_practice_hardening import GOOD, SEEDS, WEAK, scripted
from tests.test_program import TODAY

APP = Path(__file__).resolve().parent.parent / "app"
RUNNER = Path(__file__).resolve().parents[2] / "apps" / "executor" / "lib"
HEBREW = re.compile(r"[֐-׿]")
LATIN_WORD = re.compile(r"[A-Za-z]{2,}")
USER = uuid.uuid4()


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def practice(catalog, provider=None, **config) -> tuple[PracticeService, InMemoryStore]:
    store = InMemoryStore(catalog)
    return PracticeService(store, catalog, provider or scripted([GOOD] * 6),
                           ServiceConfig(suggest_reviewed_only=False, **config)), store


async def goal(svc, user=USER, job_type="digital_design"):
    await svc.save_goal(user, job_type=job_type, interview_date=TODAY + timedelta(days=10), minutes_per_day=60,
                        seniority="student")


# ----------------------------------------------------------------------------- 1. skill names


class TestSkillNames:
    def test_every_skill_and_subject_has_a_hebrew_name(self, catalog):
        assert len(catalog.skills) == 41
        for key, skill in catalog.skills.items():
            assert skill.label_he and HEBREW.search(skill.label_he), key
            assert skill.name("he") == skill.label_he and skill.name("en") == skill.label and skill.name() == skill.label
        names = [s.label_he for s in catalog.skills.values()]
        assert len(set(names)) == len(names)                                   # no two skills share a Hebrew name
        assert catalog.skill_labels() == catalog.skill_labels("en") == {k: s.label for k, s in catalog.skills.items()}
        assert catalog.skill_labels("he")["counters"] == "מונים"

    def test_a_skill_without_a_hebrew_name_falls_back_to_english(self, catalog):
        bare = catalog.skills["counters"].model_copy(update={"label_he": None})
        assert bare.name("he") == "Counters"

    def test_the_words_agree_with_the_glossary_and_the_web_apps_subjects(self, catalog):
        he = catalog.skill_labels("he")
        assert "רגיסטר" in he["registers_shifters"] and "מוקס" in he["combinational_blocks"]     # seeds/glossary.json
        assert "משלים ל-2" in he["number_representation"] and "גלישה" in he["binary_arithmetic"]
        assert he["fsms"] == "מכונות מצבים" and he["sequential_logic"] == "לוגיקה סדרתית"       # apps/web practice-ui.ts

    async def test_progress_readiness_and_the_program_name_skills_in_the_request_language(self, catalog):
        svc, _ = practice(catalog)
        await goal(svc)
        for language, same in (("he", "label_he"), ("en", "label")):
            def expected(key, same=same):
                return getattr(catalog.skills[key], same)
            progress = await svc.progress(USER, language=language)
            assert progress.focus_skills and all(s.label == expected(s.key) for s in progress.focus_skills)
            assert progress.subjects and all(s.label == expected(s.key) for s in progress.subjects)
            assert all(s.label == expected(s.key) for i in progress.plan.items for s in i.skills)
            readiness = await svc.readiness(USER, language=language)
            assert readiness.skills and all(r.label == expected(r.key) for r in readiness.skills)
            assert readiness.next_questions
            for q in readiness.next_questions:
                assert q.skill_label == expected(q.skill) and q.skill_label in q.reason
            program = await svc.program(USER, language=language)
            assert program.plan.items and all(s.label == expected(s.key) for i in program.plan.items for s in i.skills)

    async def test_english_views_carry_no_hebrew_and_hebrew_skill_rows_no_english_name(self, catalog):
        svc, _ = practice(catalog, scripted([GOOD] * 6))
        await goal(svc)
        attempt = await svc.start(USER, question_key="example-mod-six-counter", language="he")
        await svc.submit(USER, uuid.UUID(attempt.id), "תשובה", idempotency_key="k1")
        english = await svc.progress(USER, language="en")
        assert not HEBREW.search(" ".join(s.label for s in english.skills + english.focus_skills))
        assert not HEBREW.search(" ".join(i.reason for i in english.plan.items))
        hebrew = await svc.progress(USER, language="he")
        english_names = {s.label for s in catalog.skills.values()}
        assert hebrew.skills and not ({s.label for s in hebrew.skills + hebrew.focus_skills} & english_names)

    async def test_the_suggestion_after_an_answer_names_skills_in_the_attempts_language(self, catalog):
        svc, _ = practice(catalog, scripted([WEAK, WEAK]))
        attempt = await svc.start(USER, question_key="example-setup-hold-calculation", language="he")
        _, attempt = await svc.submit(USER, uuid.UUID(attempt.id), "זמן ה-hold הוא מחזור השעון", idempotency_key="k1")
        reason = attempt.next_question.reason
        assert catalog.skills[attempt.next_question.skill].label_he in reason or "setup" in reason
        assert not (set(LATIN_WORD.findall(reason)) - {"setup", "hold", "Moore", "Mealy", "NAND", "NOR", "HDL", "CDC",
                                                       "blocking", "non", "testbench", "handshake", "trade", "offs"})

    async def test_the_interview_names_skills_in_its_own_language(self, catalog):
        for language, same in (("he", "label_he"), ("en", "label")):
            store = InMemoryStore(catalog)
            svc = InterviewService(store, catalog, interviewer([GOOD, WEAK]), InterviewConfig(reviewed_only=False, narrative=False))
            svc.clock = Clock()
            user = uuid.uuid4()
            view = await svc.start(user, duration_min=30, language=language)
            assert view.plan and all(p.label == getattr(catalog.skills[p.skill], same) for p in view.plan)
            assert view.current_turn.skill_label == getattr(catalog.skills[view.current_turn.skill], same)
            view, _ = await run_to_the_end(svc, user, view)
            report = await svc.report(user, uuid.UUID(view.id), narrative=False)
            assert report.skills and all(s.label == getattr(catalog.skills[s.key], same) for s in report.skills)
            assert all(s["label"] == getattr(catalog.skills[s["key"]], same) for s in report.subjects)
            if language == "he":                       # the plain report: no English word of ours is left
                assert " min" not in report.narrative_md and "Fit:" not in report.narrative_md
                assert "דק׳" in report.narrative_md
                assert not re.search(r"\((untouched|exploring|strong|mixed|weak|done),", report.narrative_md)
            else:
                assert not HEBREW.search(report.narrative_md) and " min" in report.narrative_md

    def test_every_sentence_that_names_a_skill_is_written_in_both_languages(self):
        for table in (plan_router.REASONS, next_question.REASONS, PracticeService.READINESS_REASONS,
                      reporter.STEP_WORDS, reporter.CHANGE_WORDS):
            assert set(table["he"]) == set(table["en"])
        for table in (plan_router.REASONS, next_question.REASONS, PracticeService.READINESS_REASONS):
            for code, sentence in table["he"].items():
                # the name follows "הנושא": no verb or prefix has to agree with a name whose gender we do not know
                assert all(found.endswith("נושא ") for found in re.findall(r"(\S*\s)\{(?:next_)?skill\}", sentence)), code


# ----------------------------------------------------------------------------- 2. which limit


def _usage_limit_calls():
    """Every `ApiError("usage_limit", ...)` and `PracticeError("usage_limit", ...)` in the application."""
    for path in sorted(APP.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call) and getattr(node.func, "id", "") in ("ApiError", "PracticeError") and node.args
                    and isinstance(node.args[0], ast.Constant) and node.args[0].value == "usage_limit"):
                reason = next((k.value for k in node.keywords if k.arg == "reason"), None)
                yield f"{path.relative_to(APP)}:{node.lineno}", reason


class TestWhichLimit:
    def test_every_usage_limit_names_a_known_reason(self):
        calls = list(_usage_limit_calls())
        assert len(calls) >= 17
        for where, reason in calls:
            assert isinstance(reason, ast.Constant) and reason.value in errors.USAGE_LIMIT_REASONS, where
        used = {reason.value for _, reason in calls} | {"rate_limit"}
        assert used == set(errors.USAGE_LIMIT_REASONS)                         # the list names nothing that cannot happen

    def test_the_reason_is_in_the_error_body_and_absent_elsewhere(self):
        assert errors._body("usage_limit", "m", reason="daily_attempts") == \
            {"error": {"code": "usage_limit", "message": "m", "reason": "daily_attempts"}}
        assert errors._body("not_found", "m") == {"error": {"code": "not_found", "message": "m"}}
        assert ApiError("usage_limit", "m", reason="coins", status=402).reason == "coins"
        assert ApiError("not_found", "m").reason is None

    async def test_over_http_the_body_carries_the_reason(self):
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient
        app = FastAPI()
        errors.install(app)

        @app.get("/limited")
        async def limited():
            raise ApiError("usage_limit", "today is used up", reason="daily_attempts", headers={"Retry-After": "60"})

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
            response = await client.get("/limited")
        assert response.status_code == 429 and response.headers["Retry-After"] == "60"
        assert response.json() == {"error": {"code": "usage_limit", "message": "today is used up", "reason": "daily_attempts"}}

    async def test_the_daily_attempts_and_the_judge_tries_say_which(self, catalog):
        svc, _ = practice(catalog, daily_attempt_limit=1)
        await svc.start(USER, question_key="example-mod-six-counter", language="en")
        with pytest.raises(ApiError) as refused:
            await svc.start(USER, question_key="example-count-set-bits", language="en")
        assert (refused.value.code, refused.value.reason, refused.value.status) == ("usage_limit", "daily_attempts", 429)

    async def test_the_request_budget_says_rate_limit(self, monkeypatch):
        from app import main
        monkeypatch.setattr(main, "RATE_LIMIT_PER_MINUTE", 1, raising=False)
        sent = []

        async def app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            sent.append(message)

        limiter = main.StreamLimits(app)
        scope = {"type": "http", "method": "GET", "path": "/v1/questions", "headers": [], "query_string": b"",
                 "client": ("8.8.8.8", 1)}
        await limiter(scope, receive, send)
        sent.clear()
        await limiter(scope, receive, send)
        body = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
        assert b'"reason":"rate_limit"' in body and b'"code":"usage_limit"' in body


# ----------------------------------------------------------------------------- 3. the check's sentence


TRUTH_TABLE = {"type": "truth_table", "spec": {"variables": ["A", "B", "C"], "minterms": [3, 5, 6, 7], "output_name": "alarm"}}
NUMERIC = {"type": "numeric", "spec": {"expected": 1.4, "unit": "ns", "tolerance_abs": 0.01, "output_names": ["Tmin"]}}
ANSWERS = [
    (TRUTH_TABLE, "alarm = AB + AC + BC"), (TRUTH_TABLE, "alarm = A ^ B ^ C"), (TRUTH_TABLE, "I am not sure"),
    (TRUTH_TABLE, "alarm = A & (B"), (TRUTH_TABLE, "alarm = A & D"), (TRUTH_TABLE, "alarm = A $ B"),
    (TRUTH_TABLE, {"outputs": [0, 1]}), (TRUTH_TABLE, {}),
    (NUMERIC, "Tmin = 1.40 ns"), (NUMERIC, "Tmin = 1.22 ns"), (NUMERIC, "Tmin = 714 MHz"), (NUMERIC, "it is fast"),
    ({"type": "numeric", "spec": {"expected": 3}}, "no digits here"),
    ({"type": "code_tests", "spec": {"cases": [{"args": [0], "expected": 0}]}}, "```python\ndef f(n): return 0\n```"),
    ({"type": "sim", "spec": {}}, "x"),
]
PARSE_MESSAGES = [
    "unexpected character '$' at position 4", "unknown variable 'D'", "unexpected token ')'", "unexpected end of expression",
    "more than 64 nested parentheses", "missing closing parenthesis", "expression longer than 2000 characters",
    "no Boolean expression over A, B was found in the answer", "invalid truth table headers",
    "the input columns must match A, B", "unexpected number of rows or outputs",
    "the expected output column could not be identified", "invalid truth table row", "some required output cells are empty",
    "table has 2 rows, expected 8", "no expression or table in the answer",
]
SERVICE_MESSAGES = [
    "No verified execution result is available. The isolated runner is temporarily unavailable.",
    "No execution was performed: the code execution daily allowance has been reached",
    "No execution was performed: please wait before running code again",
    "No execution was performed: the code runner is busy; please retry shortly",
    "No execution result arrived in time; the answer is reviewed as written.",
    "The isolated runner is unavailable; code is saved and reviewed without execution.",
    "Code execution is unavailable.", checks.CODE_EXECUTION_UNAVAILABLE,
]


def told_in_hebrew(sentence: str) -> str:
    told = check_text.in_language(sentence, "he")
    assert told != sentence and HEBREW.search(told), sentence
    return told


class TestTheChecksSentence:
    def test_english_and_unknown_sentences_are_left_alone(self):
        for spec, answer in ANSWERS:
            detail = checks.run_check(spec, answer).detail
            assert check_text.in_language(detail, "en") == detail == check_text.in_language(detail, None)
        assert check_text.in_language("a sentence nobody wrote a translation for", "he") == \
            "a sentence nobody wrote a translation for"
        assert check_text.in_language(None, "he") == "" and check_text.in_language("", "he") == ""

    def test_every_sentence_the_checks_produce_is_told_in_hebrew(self):
        seen = set()
        for spec, answer in ANSWERS:
            result = checks.run_check(spec, answer)
            seen.add((result.type, result.passed))
            told = told_in_hebrew(result.detail)
            # the candidate's own symbols and numbers survive; no English sentence does
            assert not re.search(r"\b(the|was|could|not|expected|answer|rows|within|found)\b", told), told
        assert {("truth_table", True), ("truth_table", False), ("truth_table", None), ("numeric", True),
                ("numeric", False), ("numeric", None)} <= seen

    def test_the_numbers_and_names_are_carried_over(self):
        assert check_text.in_language("matches all 8 specified rows", "he") == "התשובה תואמת את כל 8 השורות שהוגדרו"
        assert check_text.in_language("2 of 8 specified rows differ", "he") == "2 מתוך 8 השורות שהוגדרו שונות"
        assert check_text.in_language("expected 1.4 ns, got 1.22 ns", "he") == "הערך הצפוי 1.4 ns, התקבל 1.22 ns"
        assert "Tmin" in check_text.in_language("no value named Tmin was found in the answer", "he")
        assert "Hz" in check_text.in_language("unit mismatch: expected s, got Hz", "he")

    def test_every_reason_an_answer_could_not_be_read(self):
        source = (APP / "engine" / "checks.py").read_text(encoding="utf-8")
        # a new message needs its Hebrew too ("unexpected token" is raised in two places)
        assert source.count("raise BooleanParseError(") == len(PARSE_MESSAGES) + 1
        general = "לא הצלחנו לקרוא את התשובה"
        for message in PARSE_MESSAGES:
            told = told_in_hebrew(f"could not parse the answer: {message}")
            assert told.startswith(general + ": ") and not re.search(r"[a-z]{4,} [a-z]{4,}", told), message
        assert check_text.in_language("could not parse the answer: something new", "he") == general

    def test_the_code_services_sentences(self):
        for message in SERVICE_MESSAGES:
            assert not LATIN_WORD.search(told_in_hebrew(message)), message
        assert check_text.in_language("No execution was performed: some new refusal", "he") == "הקוד לא הורץ"

    def test_every_sentence_the_runner_can_send_has_its_hebrew(self):
        """The runner is a separate service (apps/executor) with its own English texts: when one is added there,
        this fails until check_text knows it."""
        if not RUNNER.exists():
            pytest.skip("the runner's source is not in this checkout")
        details = []
        for name in ("runner.mjs", "job.mjs"):
            source = (RUNNER / name).read_text(encoding="utf-8")
            details += [m[2] for m in re.finditer(r"detail: ([\"`])(.+?)\1", source)]
        assert len(details) >= 14
        for detail in details:
            sentence = re.sub(r"\$\{[^}]*\}", "3", detail)
            assert not re.search(r"[A-Za-z]{2,}", told_in_hebrew(sentence).replace("HDL", "").replace("elaboration", "")), detail

    def test_the_test_scope_follows_in_the_questions_hebrew(self):
        from app.config import get_settings
        service = CodeExecutionService(get_settings().model_copy(update={"seeds_dir": SEEDS}))
        contract = service.fixtures["example-count-set-bits"]["contract"]
        stored = "5/5 question tests passed." + check_text.SCOPE_MARK + contract["en"]
        assert check_text.in_language(stored, "he") == "5 מתוך 5 בדיקות השאלה עברו.\nהיקף הבדיקה האוטומטית: " + contract["he"]
        assert check_text.in_language(stored, "en") == stored
        unknown = "5/5 question tests passed." + check_text.SCOPE_MARK + "a scope nobody translated"
        assert check_text.in_language(unknown, "he").endswith("היקף הבדיקה האוטומטית: a scope nobody translated")

    def test_a_stored_run_keeps_everything_but_its_sentence(self):
        run = {"status": "failed", "language": "python", "detail": "2/5 question tests passed.", "stdout": "x", "cases": [1]}
        told = check_text.execution_in_language(run, "he")
        assert told == {**run, "detail": "2 מתוך 5 בדיקות השאלה עברו."} and run["detail"].endswith("passed.")
        assert check_text.execution_in_language(run, "en") is run and check_text.execution_in_language(None, "he") is None
        from app.schemas.execution import ExecutionResult
        result = ExecutionResult(status="timeout", language="python", detail="Test 2 exceeded its time limit.")
        assert check_text.execution_in_language(result, "he").detail == "בדיקה 2 חרגה ממגבלת הזמן."
        assert result.detail == "Test 2 exceeded its time limit."

    async def test_a_hebrew_attempt_reads_the_check_in_hebrew_and_the_record_stays_english(self, catalog):
        for language in ("he", "en"):
            svc, store = practice(catalog, scripted([GOOD] * 4))
            user = uuid.uuid4()
            attempt = await svc.start(user, question_key="example-sensor-majority", language=language)
            submission, view = await svc.submit(user, uuid.UUID(attempt.id), "alarm = A ^ B ^ C", idempotency_key="k1")
            english = "6 of 8 specified rows differ"
            assert submission.check.passed is False and view.submission.check.detail == submission.check.detail
            assert submission.check.detail == ("6 מתוך 8 השורות שהוגדרו שונות" if language == "he" else english)
            again = await svc.get(user, uuid.UUID(attempt.id))
            assert again.submission.check.detail == submission.check.detail
            assert submission.check.mismatches                                   # the rows themselves are data, untouched
            async with store.transaction() as tx:
                stored = await tx.load_attempt(uuid.UUID(attempt.id), user_id=user)
            assert stored.row["submissions"][0]["check"]["detail"] == english    # what the judge read

    def test_the_plain_feedback_card_tells_the_check_in_the_attempts_language(self, catalog):
        from app.engine import feedback
        from app.schemas.engine import Band, Evaluation
        question = catalog.questions["example-sensor-majority"]
        check = checks.run_check(TRUTH_TABLE, "alarm = A ^ B ^ C")
        evaluation = Evaluation.model_validate(WEAK)
        hebrew = feedback.fallback_card(question, evaluation, Band.WEAK, check, "he").what_happened
        assert "6 מתוך 8 השורות שהוגדרו שונות." in hebrew and "specified rows" not in hebrew
        assert "6 of 8 specified rows differ." in feedback.fallback_card(question, evaluation, Band.WEAK, check, "en").what_happened


# ----------------------------------------------------------------------------- 4. the plan's reasons


class TestThePlansReasons:
    def names(self, catalog):
        return {language: catalog.skill_labels(language) for language in LANGUAGES}

    def test_every_reason_for_every_skill_is_retold_both_ways(self, catalog):
        names = self.names(catalog)
        facts = {"retention_due": {"level": 3}, "stale": {"level": 2, "days": 28}, "core_gap": {"level": 1, "required": 3},
                 "gap": {"level": 2, "required": 4}, "unassessed": {}, "expired": {"level": 2, "days": 50},
                 "keep_sharp": {"level": 4}}
        for key in catalog.leaf_skills:
            for code, values in facts.items():
                activity = Activity("quick", [key], 10, reason_code=code, reason_facts={"skill": key, **values})
                english = plan_router.reason_text(activity, "en", names["en"])
                hebrew = plan_router.reason_text(activity, "he", names["he"])
                assert names["he"][key] in hebrew and names["en"][key] in english
                assert plan_router.retell_reason(english, [key], "he", names) == hebrew, (key, code)
                assert plan_router.retell_reason(hebrew, [key], "en", names) == english, (key, code)
                assert plan_router.retell_reason(english, [key], "en", names) == english
                assert plan_router.retell_reason(hebrew, [key], "he", names) == hebrew

    def test_reasons_without_a_skill_and_sentences_it_does_not_know(self, catalog):
        names = self.names(catalog)
        for code in ("diagnostic", "simulation"):
            english, hebrew = plan_router.REASONS["en"][code], plan_router.REASONS["he"][code]
            assert plan_router.retell_reason(english, ["counters", "fsm_state_tables"], "he", names) == hebrew
            assert plan_router.retell_reason(hebrew, [], "en", names) == english
        old = "Counters היא מיומנות ליבה לתפקיד היעד, ואתם ברמה 1 מתוך 3 שנדרשת."      # the wording before 2026-11-19
        assert plan_router.retell_reason(old, ["counters"], "en", names) == old
        assert plan_router.retell_reason("-", ["counters"], "he", names) == "-"
        # a gap without a level is told as "no evidence yet", in both directions
        thin = Activity("quick", ["counters"], 10, reason_code="core_gap", reason_facts={"skill": "counters", "level": None})
        assert plan_router.retell_reason(plan_router.reason_text(thin, "en", names["en"]), ["counters"], "he", names) == \
            plan_router.REASONS["he"]["unassessed"].format(skill="מונים")

    async def test_a_plan_built_in_one_language_is_read_in_the_other(self, catalog):
        svc, store = practice(catalog)
        await goal(svc)
        hebrew = await svc.program(USER, language="he")                         # the day's first build: Hebrew
        assert hebrew.plan.items and all(HEBREW.search(i.reason) for i in hebrew.plan.items)
        saved = [item.reason for item in store.plans[USER].items]
        english = await svc.program(USER, language="en")                        # the same saved plan, read in English
        assert [i.id for i in english.plan.items] == [i.id for i in hebrew.plan.items]
        assert all(i.reason and not HEBREW.search(i.reason) for i in english.plan.items)
        assert english.next is not None and not HEBREW.search(english.next.reason)
        progress = await svc.progress(USER, language="en")
        assert [i.reason for i in progress.plan.items] == [i.reason for i in english.plan.items]
        back = await svc.program(USER, language="he")
        assert [i.reason for i in back.plan.items] == [i.reason for i in hebrew.plan.items]
        assert [item.reason for item in store.plans[USER].items] == saved     # reading never rewrites the plan

    async def test_and_the_other_way_round(self, catalog):
        svc, _ = practice(catalog)
        user = uuid.uuid4()
        await goal(svc, user)
        english = await svc.program(user, language="en")
        hebrew = await svc.program(user, language="he")
        assert all(not HEBREW.search(i.reason) for i in english.plan.items)
        assert all(HEBREW.search(i.reason) for i in hebrew.plan.items)
        names = catalog.skill_labels("he")
        for item in hebrew.plan.items:
            if len(item.skills) == 1 and "{skill}" in "".join(plan_router.REASONS["he"].values()):
                assert names[item.skills[0].key] in item.reason or item.mode in ("simulation", "diagnostic")
