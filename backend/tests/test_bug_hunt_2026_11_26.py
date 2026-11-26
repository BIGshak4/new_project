"""The first fixes after the bug hunt of 2026-11-26.

1. The truth-table check graded a fragment of the answer when a spelling was not one of its tokens.
2. A level-3 hint or a core misconception capped a skill's level for good.
3. The numeric check was quadratic in the length of the answer.
4. The numeric check picked the wrong number out of a correct answer, and misread common spellings.
5. The answers written outside the CORS layer (429, 413, 500) carried no cross-origin header.
6. Five sentences of the code runner had no Hebrew (pinned in test_language_backend_2026_11_19.py).
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from app import main
from app.engine import check_text, scores
from app.engine.checks import (
    NOT_ONE_VALUE,
    BooleanParseError,
    check_numeric,
    check_truth_table,
    extract_expression,
    locate_named_value,
    truth_table,
)
from app.schemas.engine import Band, SkillState
from tests.conftest import make_evaluation

ABC = ["A", "B", "C"]
MAJORITY = {"variables": ABC, "minterms": [3, 5, 6, 7], "output_name": "F"}


# ----------------------------------------------------------------------------- 1. the truth-table check


class TestTheWholeExpressionIsGradedOrNothing:
    @pytest.mark.parametrize("spelling", [
        "AB + AC’",                    # the apostrophe a phone types
        "AB + AC‘", "AB + ACʼ", "AB + AC′", "AB + AC´",
        "A ⋅ B + A ⋅ C'", "A∙B + A•C'", "A×B + A×C'",
        "A∧B ∨ A∧¬C",
        "A & B | A & !C",
    ])
    def test_every_keyboards_spelling_is_the_same_function(self, spelling):
        assert truth_table(spelling, ABC) == truth_table("AB + AC'", ABC)

    def test_xnor_nand_nor_and_the_conditional(self):
        assert truth_table("A xnor B", ABC) == truth_table("~(A ^ B)", ABC)
        assert truth_table("A ⊙ B", ABC) == truth_table("A ~^ B", ABC) == truth_table("~(A ^ B)", ABC)
        assert truth_table("A nand B", ABC) == truth_table("~(A & B)", ABC)
        assert truth_table("A nor B", ABC) == truth_table("~(A | B)", ABC)
        assert truth_table("A NAND B NAND C", ABC) == truth_table("~(~(A & B) & C)", ABC)
        assert truth_table("A ? B : C", ABC) == truth_table("AB + A'C", ABC)
        assert truth_table("A ? B : (C & A)", ABC) == truth_table("AB", ABC)
        assert truth_table("A ? (B ? C : A) : 0", ABC) == truth_table("A(BC + B')", ABC)

    def test_a_conditional_that_is_not_finished_and_a_long_chain_are_refused(self):
        for broken in ("A ? B", "A ? B :", "A ? : C", "A : B"):
            with pytest.raises(BooleanParseError):
                truth_table(broken, ABC)
        with pytest.raises(BooleanParseError):
            truth_table("A ? B : " * 40 + "C", ABC)

    @pytest.mark.parametrize("answer", [
        "F = AB + BC + AC’B",                       # was graded as AB + BC, then failed for the wrong reason
        "F = AB + BC + AC + A’B’C’",                # was graded as AB + BC + AC and PASSED
    ])
    def test_a_wrong_answer_in_a_phones_spelling_fails(self, answer):
        assert check_truth_table(MAJORITY, answer).passed is False

    @pytest.mark.parametrize("answer", [
        "F = AB + BC + AC",
        "F = A B + B C + A C",
        "F = A⋅B + B⋅C + A⋅C",
        "A majority vote: AB + BC + AC",            # was graded as A (the article)
        "F = (A+B)(A+C)(B+C) = AB + BC + AC",       # a chain of equal forms: the last one
        "F = AB + BC + AC because any two suffice.",
        "F = AB + BC + AC, right?",
        "assign F = (A & B) | (B & C) | (A & C);",
        "notes\nA\nB\nF = AB + BC + AC",
    ])
    def test_a_right_answer_passes_however_it_is_written(self, answer):
        assert check_truth_table(MAJORITY, answer).passed is True

    @pytest.mark.parametrize("answer", [
        "F = AB + BC + AC̄",                         # a combining overline: not a token
        "F = AB + BC ⊻ AC",                         # an operator the parser does not know
        "F = AB + BC + AC implies A",
        "F = A B ⊻ C",                              # no cut may hide the unknown operator in the part left behind
        "F = A B implies C",
    ])
    def test_an_expression_it_cannot_read_to_the_end_is_not_graded(self, answer):
        """Before, the part in front of the unknown spelling was graded as the whole answer. A verdict of None
        neither caps nor lifts the judge's score."""
        result = check_truth_table(MAJORITY, answer)
        assert result.passed is None and result.detail.startswith("could not parse the answer")

    def test_the_asked_output_is_read_when_several_are_assigned_on_one_line(self):
        decoder = ["E", "A1", "A0"]
        line = "Y0=E&~A1&~A0; Y1=E&~A1&A0; Y2=E&A1&~A0; Y3=E&A1&A0"
        assert extract_expression(line, decoder, "Y2") == "E&A1&~A0"
        assert extract_expression("Y2 = E A1 A0’ Y3 = E A1 A0", decoder, "Y2") == "E A1 A0’"
        assert extract_expression("Y2 = E A1 A0’, Y3 = E A1 A0", decoder, "Y2") == "E A1 A0’"
        assert extract_expression("F = A + B = B + A", ABC, "F") == "B + A"          # variables are not another output

    def test_hostile_lengths_stay_cheap(self):
        for unit in ("A ? B : ", "F = A’", "A xnor ", "(A ? ", "A’’’", "F = A + B = ", "A ,B = "):
            started = time.process_time()
            check_truth_table(MAJORITY, (unit * 20_000)[:20_000])
            assert time.process_time() - started < 2, unit


# ----------------------------------------------------------------------------- 2. the caps on a level lapse


def practise(skill: SkillState, turns) -> SkillState:
    for difficulty, band, hint, core in turns:
        scores.record_turn(skill, difficulty=difficulty, band=band, evaluation=make_evaluation(level=4),
                           hint_level=hint, weight=1.0, core_misconception=core)
    return skill


class TestACapIsLiftedByLaterProof:
    def test_a_level3_hint_no_longer_caps_for_good(self):
        skill = practise(SkillState(key="x", k=90.0, c=60.0), [(3, Band.WEAK, 3, False)])
        assert skill.level3_hint_difficulty == 3 and scores.questioned_level(skill)[0] == 1
        practise(skill, [(8, Band.STRONG, 0, False)] * 20)
        assert skill.level3_hint_difficulty is None
        assert scores.questioned_level(skill)[0] >= 4                # it stayed at 1 before

    def test_only_proof_at_that_difficulty_lifts_the_hints_cap(self):
        skill = practise(SkillState(key="x", k=90.0, c=60.0), [(7, Band.WEAK, 3, False), (5, Band.STRONG, 0, False)])
        assert skill.level3_hint_difficulty == 7                     # strong, but on an easier question
        practise(skill, [(7, Band.PARTIAL, 0, False), (8, Band.STRONG, 3, False)])
        assert skill.level3_hint_difficulty == 7                     # partial is not proof; nor is strong with the hint
        practise(skill, [(7, Band.STRONG, 2, False)])
        assert skill.level3_hint_difficulty is None

    def test_an_answer_that_does_not_count_lifts_nothing(self):
        skill = practise(SkillState(key="x", k=90.0, c=60.0), [(4, Band.WEAK, 3, True)])
        scores.record_turn(skill, difficulty=9, band=Band.STRONG, evaluation=make_evaluation(level=5), hint_level=0,
                           weight=0.0, core_misconception=False)      # the reference was open: weight 0
        assert skill.level3_hint_difficulty == 4 and skill.core_misconception is True

    def test_a_core_misconception_is_lifted_by_one_strong_answer_and_comes_back_with_the_next_one(self):
        skill = practise(SkillState(key="x", k=95.0, c=60.0), [(7, Band.STRONG, 0, False), (8, Band.WEAK, 0, True)])
        assert skill.core_misconception is True and scores.questioned_level(skill)[0] == 2
        practise(skill, [(6, Band.PARTIAL, 0, False)])
        assert skill.core_misconception is True
        practise(skill, [(6, Band.STRONG, 0, False)])
        assert skill.core_misconception is False and scores.questioned_level(skill)[0] > 2
        practise(skill, [(6, Band.WEAK, 0, True)])
        assert skill.core_misconception is True and scores.questioned_level(skill)[0] == 2

    def test_a_second_level3_hint_after_the_lift_caps_again(self):
        skill = practise(SkillState(key="x", k=90.0, c=60.0),
                         [(5, Band.WEAK, 3, False), (6, Band.STRONG, 0, False), (8, Band.WEAK, 3, False)])
        assert skill.level3_hint_difficulty == 8


# ----------------------------------------------------------------------------- 3 and 4. the numeric check


def numeric(expected, names, unit=None, **spec):
    return {"expected": expected, "output_names": names, **({"unit": unit} if unit else {}), **spec}


TMIN = numeric(1.4, ["Tmin", "T_min", "minimum clock period", "min period", "period"], "ns", tolerance_abs=0.01)


class TestTheNumericCheckIsBounded:
    @pytest.mark.parametrize("unit", ["Tmin=1 ", "Tmin = 1 ", "Tmin1ns", "Tmin ", "Tmin = (", "period Tmin = 1+",
                                      "Tmin = 1 x 10^", "1,000,", "Tmin = a = "])
    def test_twenty_thousand_characters_cost_a_fraction_of_a_second(self, unit):
        """`Tmin=1 ` repeated took 7.5 s of processor time at 10,000 characters and about a minute at 20,000."""
        started = time.process_time()
        check_numeric(TMIN, (unit * 20_000)[:20_000])
        assert time.process_time() - started < 2, unit

    def test_the_last_statement_of_a_long_answer_is_still_the_one_read(self):
        answer = "Tmin = 9 ns. " * 1500 + "After the fix, Tmin = 1.4 ns."
        assert check_numeric(TMIN, answer).passed is True


class TestWhichNumberIsTheAnswer:
    @pytest.mark.parametrize("spec, answer, passed", [
        # a name is a whole word
        (numeric(107, ["c"]), "c = 107 because a = 5 and b = 102 at edge 2", True),
        (numeric(8, ["x"]), "x = 8 after the fourth edge. On the next edge it becomes 13.", True),
        (numeric(8, ["x"]), "After 4 edges x = 8, the next value is 13", True),
        (numeric(-31, ["acc"]), "acc = -31. The accumulator is 6 bits wide.", True),
        # the occurrence that links the name to a value is believed over one that stands next to a number
        (numeric(4, ["N", "number of flip-flops", "stages"]), "N = 4, since 3 stages give an MTBF of only 2 years", True),
        (numeric(4, ["N", "number of flip-flops", "stages"]), "We need N = 4 stages. With 3 the MTBF is under 10 years.", True),
        # brackets are an aside, and a literal of another base is not a second value
        (TMIN, "Tmin = 1.40 ns (tcq 0.12 ns + tcomb 1.10 ns + tsetup 0.18 ns)", True),
        (numeric(-31, ["acc"]), "acc = -31 (100001 in six bits)", True),
        (numeric(-274, ["sum", "result"]), "sum = -274 (0xEEE)", True),
        (numeric(-274, ["sum", "result"]), "sum = 0xEEE = -274", True),
        (numeric(-274, ["sum", "result"]), "result = -274 in 12 bits", True),
        (numeric(0.6, ["slack"], "ns", tolerance_abs=0.01), "The setup slack at FF2 is 0.6 ns after borrowing 0.4 ns", True),
        # a chain of equals: what follows the last one; an annotated number continues the chain
        (TMIN, "Tmin = tcq + tcomb + tsetup = 0.12 + 1.10 + 0.18 = 1.40 ns", True),
        (numeric(-31, ["acc"]), "acc = 33 unsigned = -31 signed", True),
        (numeric(107, ["c"]), "c = 107 = a + b", True),
        # wrong stays wrong when no number near the name is the expected one
        (numeric(107, ["c"]), "c = 99", False),
        (TMIN, "Tmin = 1.10 + 0.18 = 1.28 ns, so fmax = 781 MHz.", False),
        (TMIN, "Tmin = 714 MHz", False),
        # doubt is not a verdict
        (TMIN, "Tmin = 2.0 ns (the book says 1.4 ns but I think that is wrong)", None),
        (TMIN, "Tmin = 0.12 + 1.10 + 0.18 ns", None),
        (TMIN, "Tmin = 1.4 + 0.6 ns", None),
        (numeric(8, ["x"]), "x after edge 4 is 8", None),
        (TMIN, "fmax = 714 MHz; the rest follows", None),
    ])
    def test_the_stated_value(self, spec, answer, passed):
        assert check_numeric(spec, answer).passed is passed, check_numeric(spec, answer).detail

    def test_doubt_says_so_in_both_languages(self):
        result = check_numeric(TMIN, "Tmin = 2.0 ns (the book says 1.4 ns)")
        assert result.passed is None and result.detail == NOT_ONE_VALUE.format(names=", ".join(TMIN["output_names"]))
        told = check_text.in_language(result.detail, "he")
        assert told.startswith("בתשובה יש יותר מערך אחד") and "checked" not in told
        assert check_text.in_language(result.detail, "en") == result.detail

    def test_locate_named_value_keeps_its_contract(self):
        assert locate_named_value("Tmin = 1.40 ns, so fmax = 714 MHz", ["Tmin"]) == "1.40 ns"
        assert locate_named_value("Tmin = 0.12 + 1.10 + 0.18 = 1.40 ns", ["Tmin"], expected_base="s", base_units={"s"}) == "1.40 ns"
        assert locate_named_value("because next since", ["c", "x", "N"]) is None
        assert locate_named_value("Tmin = 0.12 + 1.10", ["Tmin"]) is None


class TestHowANumberIsWritten:
    @pytest.mark.parametrize("answer", [
        "Tmin = 1.4 ns", "Tmin = 1,4 ns", "Tmin=1.4ns", "tmin = 1.4 ns", "Tmin = 1400 ps", "Tmin = 1,400 ps",
        "Tmin = 1400 picoseconds", "Tmin = 1400 psec", "Tmin = 1.4 nanoseconds", "Tmin = 1.4 nsec",
        "Tmin = 1.4e-9 s", "Tmin = 1.4e-9 seconds", "Tmin = 1.4 x 10^-9 s", "Tmin = 1.4 × 10^(-9) s", "Tmin = 1.4*10^-9 s",
    ])
    def test_the_same_period_in_every_spelling(self, answer):
        assert check_numeric(TMIN, answer).passed is True, check_numeric(TMIN, answer).detail

    @pytest.mark.parametrize("spec, answer, passed", [
        (numeric(1493, ["MTBF"], "years"), "MTBF = 1,493 years", True),           # a digit group, read as 1.493 before
        (numeric(1493, ["MTBF"], "years"), "MTBF = 1,493,000 years", False),
        (numeric(100, ["f"], "MHz"), "f = 100,000 kHz", True),
        (numeric(100, ["f"], "MHz"), "f = 10^8 Hz", True),
        (numeric(-31, ["acc"]), "acc = −31", True),                               # the typographic minus
        (numeric(-31, ["acc"]), "acc = 31", False),
        (numeric(0.6, ["slack"], "ns", tolerance_abs=0.01), "slack = .6 ns", True),
        (numeric(4.7, ["R"], "kΩ"), "R = 4.7 kohm", True),
        (numeric(4.7, ["R"], "kΩ"), "R = 4700 ohms", True),
        (numeric(16, ["width"], "bits"), "width = 16 bit", True),
        (numeric(3.3, ["Vdd"], "V", tolerance_abs=0.1), "Vdd = 3.4 V", True),     # 3.4 - 3.3 > 0.1 in floating point
        (numeric(3.3, ["Vdd"], "V", tolerance_abs=0.1), "Vdd = 3.41 V", False),
    ])
    def test_digit_groups_signs_units_and_the_edge_of_the_tolerance(self, spec, answer, passed):
        assert check_numeric(spec, answer).passed is passed, check_numeric(spec, answer).detail

    def test_without_names_the_check_is_as_it_was(self):
        spec = {"expected": 12.5, "unit": "ns", "tolerance_abs": 0.1}
        assert check_numeric(spec, "12.5").passed is True and check_numeric(spec, "12500 ps").passed is True
        assert check_numeric(spec, "12.5 ms").passed is False and check_numeric({"expected": 5, "unit": "ns"}, "5 MHz").passed is False
        assert check_numeric({"expected": 5}, "about five").passed is None
        assert check_numeric({"expected": 1000}, 1009).passed is True and check_numeric({"expected": 1000}, 1011).passed is False


# ----------------------------------------------------------------------------- 5. answers written outside the CORS layer


SITE = "https://site.example"


async def respond_ok(scope, receive, send):
    await send({"type": "http.response.start", "status": 204, "headers": []})
    await send({"type": "http.response.body", "body": b""})


async def call(limiter, *, origin: str | None, body: bytes = b"", token: str = "same") -> tuple[int, dict[str, str]]:
    messages = []
    headers = [(b"authorization", f"Bearer {token}".encode())] + ([(b"origin", origin.encode())] if origin else [])
    scope = {"type": "http", "method": "POST", "path": "/v1/me/goal", "query_string": b"", "scheme": "https",
             "client": ("192.0.2.10", 50000), "headers": headers}

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    await limiter(scope, receive, send)
    start = next(message for message in messages if message["type"] == "http.response.start")
    return start["status"], {name.decode().lower(): value.decode() for name, value in start["headers"]}


class TestAnswersOutsideTheCorsLayer:
    @pytest.fixture(autouse=True)
    def allowed(self, monkeypatch):
        monkeypatch.setattr(main, "get_settings", lambda: SimpleNamespace(allowed_origins=[SITE]))

    def test_the_header_goes_to_an_allowed_origin_and_to_nobody_else(self):
        assert main.cors_headers(SITE) == {"Access-Control-Allow-Origin": SITE,
                                           "Access-Control-Expose-Headers": "X-Request-Id", "Vary": "Origin"}
        assert main.cors_headers("https://evil.example") == {} and main.cors_headers(None) == {} and main.cors_headers("") == {}

    def test_an_open_api_answers_with_the_wildcard(self, monkeypatch):
        monkeypatch.setattr(main, "get_settings", lambda: SimpleNamespace(allowed_origins=["*"]))
        assert main.cors_headers("https://anything.example")["Access-Control-Allow-Origin"] == "*"

    async def test_the_rate_limits_429_can_be_read_by_the_web_app(self, monkeypatch):
        monkeypatch.setattr(main, "RATE_LIMIT_PER_MINUTE", 3)
        limiter = main.StreamLimits(respond_ok)
        statuses = [await call(limiter, origin=SITE) for _ in range(5)]
        status, headers = statuses[-1]
        assert status == 429 and headers["access-control-allow-origin"] == SITE and headers["retry-after"] == "60"
        status, headers = await call(limiter, origin="https://evil.example")
        assert status == 429 and "access-control-allow-origin" not in headers

    async def test_the_body_limits_413_can_be_read_by_the_web_app(self):
        async def reads_the_body(scope, receive, send):
            await receive()
            await respond_ok(scope, receive, send)

        limiter = main.StreamLimits(reads_the_body)
        status, headers = await call(limiter, origin=SITE, body=b"x" * (main.MAX_BODY_BYTES + 1))
        assert status == 413 and headers["access-control-allow-origin"] == SITE
        status, headers = await call(limiter, origin=None, body=b"x" * (main.MAX_BODY_BYTES + 1), token="other")
        assert status == 413 and "access-control-allow-origin" not in headers
        declared = main._too_large_response("abc123", SITE)
        assert declared.status_code == 413 and declared.headers["access-control-allow-origin"] == SITE

    async def test_the_last_resort_500_can_be_read_by_the_web_app(self):
        async def boom(request):
            raise RuntimeError("a failure nobody handled")

        request = SimpleNamespace(headers={"origin": SITE}, state=SimpleNamespace(), method="GET",
                                  url=SimpleNamespace(path="/v1/me"))
        response = await main.request_log(request, boom)
        assert response.status_code == 500 and response.headers["access-control-allow-origin"] == SITE
        assert response.headers["x-request-id"] == request.state.request_id
