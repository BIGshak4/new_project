"""Four deterministic overnight contracts and independent private expectations.

Native C++ execution and compiler errors are verified separately in microVMs.
These tests execute only repository-controlled Python references.
"""
from __future__ import annotations

import ast
import copy
import json
import runpy
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
AUTHORING = runpy.run_path(str(BACKEND / "tests/fixtures/execution_catalog_authoring.py"))
INPUTS = json.loads((BACKEND / "tests/fixtures/execution_night1107n30_inputs.json").read_bytes())
MANIFEST = json.loads((BACKEND / "seeds/execution_cases.json").read_bytes())["questions"]
POSITIVE = json.loads((BACKEND / "tests/fixtures/execution_positive.json").read_bytes())["cases"]
SMOKE = json.loads((BACKEND / "tests/fixtures/execution_smoke.json").read_bytes())["cases"]
COUNTS = {"prep-longest-ones-interval": 12, "prep-cpp-atoi-style-parser": 20,
          "prep-black-component-bounding-boxes": 12, "prep-monotone-grid-paths-dp": 12}
PYTHON_CASES = [(key, case) for key in COUNTS if key != "prep-cpp-atoi-style-parser"
                for case in MANIFEST[key]["languages"]["python"]["cases"]]


def reference(key):
    fixture = next(row for row in POSITIVE if row["question_key"] == key)
    namespace = {}
    exec(compile(fixture["source"], "<trusted-night30-reference>", "exec"), namespace)
    return namespace[MANIFEST[key]["languages"]["python"]["entry"]]


@pytest.mark.parametrize("key", COUNTS)
def test_inputs_are_answer_free_and_expected_values_use_independent_oracles(key):
    assert set(INPUTS) == set(AUTHORING["NIGHT1107N30_ORACLES"]) == set(COUNTS)
    language = "cpp" if key == "prep-cpp-atoi-style-parser" else "python"
    given = INPUTS[key]["languages"][language]
    built = MANIFEST[key]["languages"][language]
    assert len(given["cases"]) == len(built["cases"]) == COUNTS[key]
    field = "stdin" if language == "cpp" else "args"
    expected_field = "expected_stdout" if language == "cpp" else "expected"
    assert all(set(case) == {field} for case in given["cases"])
    assert [case[field] for case in given["cases"]] == [case[field] for case in built["cases"]]
    for case in built["cases"]:
        oracle = AUTHORING["NIGHT1107N30_ORACLES"][key]
        expected = oracle(case["stdin"]) if language == "cpp" else oracle(*case["args"])
        assert expected == case[expected_field]


@pytest.mark.parametrize("key,case", PYTHON_CASES)
def test_trusted_python_reference_matches_each_private_case_without_mutating_input(key, case):
    args = copy.deepcopy(case["args"])
    assert reference(key)(*args) == case["expected"]
    assert args == case["args"]


@pytest.mark.parametrize("key", [key for key in COUNTS if key != "prep-cpp-atoi-style-parser"])
def test_wrong_and_syntax_python_fixtures_fail(key):
    fixture = next(row for row in SMOKE if row["question_key"] == key)
    with pytest.raises(SyntaxError):
        compile(fixture["syntax_error"], "<intentional-invalid-night30>", "exec")
    namespace = {}
    exec(compile(fixture["wrong"], "<trusted-intentional-wrong-night30>", "exec"), namespace)
    candidate = namespace[MANIFEST[key]["languages"]["python"]["entry"]]
    assert any(candidate(*copy.deepcopy(case["args"])) != case["expected"]
               for case in MANIFEST[key]["languages"]["python"]["cases"])


def test_domain_rejection_and_inclusive_tie_rules():
    longest = reference("prep-longest-ones-interval")
    for values in ([2], [True], None):
        with pytest.raises(ValueError):
            longest(values)
    assert longest([1, 1, 0, 1, 1]) == [0, 1]
    assert longest([0, 1, 1]) == [1, 2]
    boxes = reference("prep-black-component-bounding-boxes")
    for image in ([[]], [[1], []], [[True]], [[2]]):
        before = copy.deepcopy(image)
        with pytest.raises(ValueError):
            boxes(image)
        assert image == before
    for n in (0, -1, True):
        with pytest.raises(ValueError):
            reference("prep-monotone-grid-paths-dp")(n)


def test_connectivity_order_and_box_overlap_do_not_change_component_identity():
    boxes = reference("prep-black-component-bounding-boxes")
    assert boxes([[1, 0], [0, 1]]) == [[0, 0, 0, 0], [1, 1, 1, 1]]
    ring = [[int(r in (0, 4) or c in (0, 4) or (r == c == 2))
             for c in range(5)] for r in range(5)]
    assert boxes(ring) == [[0, 0, 4, 4], [2, 2, 2, 2]]


def test_grid_reference_uses_dynamic_programming_and_wide_exact_counts():
    source = AUTHORING["night1107n30_source"]("prep-monotone-grid-paths-dp")
    tree = ast.parse(source)
    assert not any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(tree))
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id in {"comb", "factorial"} for node in ast.walk(tree))
    assert reference("prep-monotone-grid-paths-dp")(1) == 1
    assert reference("prep-monotone-grid-paths-dp")(18) > (1 << 31) - 1


def test_cpp_driver_reads_entire_stdin_and_private_cases_cover_grammar_and_clamping():
    key = "prep-cpp-atoi-style-parser"
    spec = MANIFEST[key]["languages"]["cpp"]
    driver = spec["driver"]
    assert '#define JOBRUN_PREP295_NO_MAIN' in driver
    assert '#include "solution.cpp"' in driver
    assert "std::istreambuf_iterator<char>(std::cin)" in driver
    assert "getline" not in driver
    assert "expected" not in driver
    cases = {case["stdin"]: case["expected_stdout"] for case in spec["cases"]}
    assert cases["\n\t+17 rest"] == "17\n"
    assert cases["2147483648"] == "2147483647\n"
    assert cases["-2147483649"] == "-2147483648\n"
    assert cases["+"] == "0\n"
    assert cases["12.34"] == "12\n"
    assert cases["\u00a042"] == "0\n"
    # The deployed broker intentionally excludes NUL from all program stdin.
    # The separate native C++ harness covers embedded-NUL parser semantics.
    assert all("\0" not in value for value in cases)
    source = AUTHORING["night1107n30_source"](key)
    assert "#ifndef JOBRUN_PREP295_NO_MAIN" in source
    assert not any(name in source for name in ("std::atoi", "std::stoi", "std::strtol"))
    assert len([row for row in POSITIVE if row["question_key"] == key]) == 1
    assert len([row for row in SMOKE if row["question_key"] == key]) == 1


def test_old_text_and_list_variants_remain_outside_the_new_profile_set():
    assert MANIFEST["prep-most-frequent-word-list"]["languages"]["python"]["entry"] == "most_frequent_word"
    assert "prep-abstract-list-head-tail-concat-reversal" not in COUNTS
    for key in COUNTS:
        assert len([row for row in POSITIVE if row["question_key"] == key]) == 1
        assert len([row for row in SMOKE if row["question_key"] == key]) == 1
