"""Validate private execution contracts/oracles, without executing learner source.

Real compiler/VM smoke checks use fixtures/execution_smoke.json separately. These
tests do not claim compilation, synthesis, complexity, or formal verification.
"""

from __future__ import annotations

import itertools
import json
import re
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

BACKEND = Path(__file__).resolve().parents[1]
AUTHORING = runpy.run_path(str(BACKEND / "tests/fixtures/execution_catalog_authoring.py"))
MANIFEST = json.loads((BACKEND / "seeds/execution_cases.json").read_text(encoding="utf-8"))
SMOKE = json.loads((BACKEND / "tests/fixtures/execution_smoke.json").read_text(encoding="utf-8"))
ORACLES = AUTHORING["ORACLES"]
QUESTIONS = MANIFEST["questions"]
LANGUAGES = {"python", "javascript", "c", "cpp", "verilog", "systemverilog", "vhdl"}
CATALOG = {
    q["key"]: q
    for filename in ("example_bank.json", "preparation_bank.json")
    for q in json.loads((BACKEND / "seeds/questions" / filename).read_text(encoding="utf-8"))
}
SPECS = [(key, language, spec) for key, question in QUESTIONS.items()
         for language, spec in question["languages"].items()]


def test_manifest_is_versioned_and_all_contracts_belong_to_current_catalog():
    assert MANIFEST["version"] == 1
    assert 20 <= len(QUESTIONS) <= 30
    assert set(QUESTIONS) <= CATALOG.keys()
    for question in QUESTIONS.values():
        assert set(question["contract"]) == {"he", "en"}
        assert re.search(r"[א-ת]", question["contract"]["he"])
        assert not re.search(r"[א-ת]", question["contract"]["en"])
        assert question["languages"]
        assert set(question["languages"]) <= LANGUAGES


@pytest.mark.parametrize("key,language,spec", SPECS, ids=[f"{key}/{lang}" for key, lang, _ in SPECS])
def test_language_specs_have_complete_safe_contract_shapes(key, language, spec):
    assert isinstance(spec["starter"], str) and spec["starter"].strip()
    if spec["kind"] == "function":
        assert language in {"python", "javascript"}
        assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", spec["entry"])
        assert spec["entry"] in QUESTIONS[key]["contract"]["en"]
        assert 1 <= len(spec["cases"]) <= 32
        for case in spec["cases"]:
            assert isinstance(case["args"], list)
            assert "expected" in case
            assert set(case) <= {"args", "expected", "unordered"}
    elif spec["kind"] == "program":
        assert language in {"c", "cpp"}
        assert f'#include "solution.{language}"' in spec["driver"]
        assert "main(" in spec["driver"]
        assert 1 <= len(spec["cases"]) <= 32
        for case in spec["cases"]:
            assert isinstance(case["stdin"], str)
            assert isinstance(case["expected_stdout"], str)
    else:
        assert spec["kind"] == "hdl"
        assert language in {"verilog", "systemverilog", "vhdl"}
        assert re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", spec["top"])
        assert spec["testbench"].strip()
        assert spec["expected_stdout"].strip()
        # Oracle comparisons belong in the trusted broker, not the learner VM.
        assert "expected_stdout" not in spec["testbench"]
        assert "$fatal" not in spec["testbench"]
        assert "assert " not in spec["testbench"]


def test_all_seven_preexisting_python_tests_keep_their_test_inputs():
    existing = {q["key"]: q["deterministic_check"]["spec"] for q in CATALOG.values()
                if (q.get("deterministic_check") or {}).get("type") == "code_tests"}
    assert len(existing) == 7
    for key, old in existing.items():
        spec = QUESTIONS[key]["languages"]["python"]
        assert spec["kind"] == "function"
        assert spec["entry"] in old["entry"]
        for old_case in old["cases"]:
            matches = [case for case in spec["cases"] if case["args"] == old_case["args"]]
            assert matches, (key, old_case["args"])
            result = matches[0]["expected"]
            acceptable = old_case.get("accept", [old_case.get("expected")])
            if old_case.get("unordered") and isinstance(result, list):
                assert sorted(result) in [sorted(x) for x in acceptable]
            else:
                assert result in acceptable


@pytest.mark.parametrize("key,language,spec", [item for item in SPECS if item[2]["kind"] == "function"])
def test_function_expected_results_match_independent_reference_models(key, language, spec):
    oracle = ORACLES[key]
    for case in spec["cases"]:
        result = oracle(*case["args"])
        if case.get("unordered"):
            assert sorted(result) == sorted(case["expected"])
        else:
            assert result == case["expected"]


@pytest.mark.parametrize("key,language,spec", [item for item in SPECS if item[2]["kind"] == "program"])
def test_c_and_cpp_driver_cases_use_the_same_independent_scalar_oracles(key, language, spec):
    for case in spec["cases"]:
        n = int(case["stdin"].strip())
        assert case["expected_stdout"] == f"{int(ORACLES[key](n))}\n"


def test_byte_boundary_patterns_and_exhaustive_truth_tables_are_not_only_happy_paths():
    for key in ("prep-reverse-exactly-eight-bits-without-array", "prep-byte-popcount-parallel-and-lookup"):
        cases = QUESTIONS[key]["languages"]["python"]["cases"]
        values = {c["args"][0] for c in cases}
        assert len(values) == 32
        assert {0, 1, 128, 255, 85, 170} <= values
        assert {1 << i for i in range(8)} <= values
    expected = [int(a + b + c >= 2) for a, b, c in itertools.product((0, 1), repeat=3)]
    for spec in QUESTIONS["example-sensor-majority"]["languages"].values():
        assert list(map(int, spec["expected_stdout"].splitlines())) == expected
    for spec in QUESTIONS["prep-eight-bit-unsigned-lower-clamp-sixty-four"]["languages"].values():
        assert list(map(int, spec["expected_stdout"].splitlines())) == [64] * 65 + list(range(65, 256))
    for spec in QUESTIONS["prep-unsigned-two-bit-combinational-square"]["languages"].values():
        assert list(map(int, spec["expected_stdout"].splitlines())) == [0, 1, 4, 9]


def test_enabled_counter_transcript_uses_legal_states_reset_priority_holds_and_wrap():
    stimuli = AUTHORING["COUNTER_STIMULUS"]
    # Independent state-transition model vs author's enabled-since-reset arithmetic.
    state = 0
    expected = []
    for reset, enabled in stimuli:
        if reset:
            state = 0
        elif enabled:
            state = (state + 1) % 6
        expected.append(state)
    assert all(0 <= state <= 5 for state in expected)
    assert any(a == 5 and b == 0 for a, b in zip(expected, expected[1:], strict=False))
    assert any(not rst and not en for rst, en in stimuli)
    assert any(rst and en for rst, en in stimuli)
    for spec in QUESTIONS["prep-enabled-mod-six-counter"]["languages"].values():
        assert list(map(int, spec["expected_stdout"].splitlines())) == expected


def test_1101_transcript_matches_independent_prefix_fsm_and_includes_overlap():
    # Longest matching prefix transition oracle; author used last-four-bit history.
    transitions = ((0, 1), (0, 2), (3, 2), (0, 4), (0, 2))
    state = 0
    expected = []
    for reset, bit in AUTHORING["SEQUENCE_STIMULUS"]:
        state = 0 if reset else transitions[state][bit]
        expected.append(int(state == 4))
    hits = [i for i, value in enumerate(expected) if value]
    assert any(b - a == 3 for a, b in zip(hits, hits[1:], strict=False)), "1101101 must exercise overlap"
    for spec in QUESTIONS["prep-serial-1101-state-storage-count"]["languages"].values():
        assert list(map(int, spec["expected_stdout"].splitlines())) == expected


@pytest.mark.parametrize("key,args,expected", [
    ("example-count-set-bits", [2147483648], 1),
    ("example-power-of-two-check", [0], False),
    ("example-extract-register-field", [4294967295, 0, 32], 4294967295),
    ("example-pair-sum-indices", [[6], 12], None),
    ("example-balanced-brackets", ["([)]"], False),
    ("prep-reverse-exactly-eight-bits-without-array", [1], 128),
    ("prep-one-active-bit-signed-int32-pattern", [-2147483648], True),
    ("prep-ascii-letter-palindrome-two-pointers", ["Aa"], False),
    ("prep-first-equal-in-sorted-array", [[1, 2], 3], -1),
    ("prep-maximum-sum-contiguous-subarray", [[-8, -2, -6]], [-2, 1, 1]),
    ("prep-maximum-sum-contiguous-subarray", [[0, 0]], [0, 0, 0]),
    ("prep-postfix-expression-stack-evaluation", [[3, 8, "-"]], -5),
    ("prep-one-two-missing-values", [[]], 0),
    ("prep-two-missing-zero-through-n-plus-one-no-aux-array", [[]], [0, 1]),
    ("prep-longest-contiguous-sum-divisible-by-three", [[1]], [0, None, None]),
])
def test_real_counterexamples_are_present_in_the_shipped_cases(key, args, expected):
    cases = QUESTIONS[key]["languages"]["python"]["cases"]
    assert {"args": args, "expected": expected} in cases or any(
        case["args"] == args and case["expected"] == expected for case in cases)


def test_smoke_fixtures_cover_correct_wrong_and_syntax_in_all_seven_languages():
    assert SMOKE["version"] == 1
    assert {case["language"] for case in SMOKE["cases"]} == LANGUAGES
    for case in SMOKE["cases"]:
        assert case["language"] in QUESTIONS[case["question_key"]]["languages"]
        assert all(isinstance(case[k], str) and case[k].strip() for k in ("correct", "wrong", "syntax_error"))
        assert len({case[k] for k in ("correct", "wrong", "syntax_error")}) == 3
    assert any(c["question_key"] == "prep-serial-1101-state-storage-count" for c in SMOKE["cases"])


def test_manifest_and_smoke_are_reproducible_author_artifacts():
    assert AUTHORING["build_manifest"]() == MANIFEST
    assert AUTHORING["build_smoke"]() == SMOKE


@pytest.mark.asyncio
async def test_backend_loads_private_specs_and_only_publishes_contracts_and_starters():
    from app.schemas.bank import BankQuestion
    from app.services.code_execution import CodeExecutionService

    settings = SimpleNamespace(code_execution_url="", code_execution_signing_seed=None,
        supabase_service_role_key=None, code_execution_enabled=False, code_execution_daily_limit=20,
        code_execution_per_minute=4, code_execution_concurrency=1, seeds_dir=BACKEND / "seeds")
    service = CodeExecutionService(settings)
    try:
        for key, question in QUESTIONS.items():
            bank_question = BankQuestion.model_validate(CATALOG[key])
            capabilities = await service.capabilities(bank_question)
            assert not capabilities.available
            assert set(capabilities.tested_languages) == set(question["languages"])
            assert capabilities.contract == question["contract"]
            for language, authored in question["languages"].items():
                spec = service.spec(bank_question, language)
                assert spec == {k: v for k, v in authored.items() if k != "starter"}
                assert capabilities.starters[language] == authored["starter"]
            public = capabilities.model_dump()
            assert "cases" not in public
            assert "testbench" not in public
            assert "expected_stdout" not in public
    finally:
        await service.aclose()
