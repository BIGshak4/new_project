"""Input-only contracts, independent oracles and trusted reference boundaries."""
from __future__ import annotations

import ast
import copy
import json
import runpy
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
AUTHORING = runpy.run_path(str(BACKEND / "tests/fixtures/execution_catalog_authoring.py"))
INPUTS = json.loads((BACKEND / "tests/fixtures/execution_batch1108b20_inputs.json").read_bytes())
MANIFEST = json.loads((BACKEND / "seeds/execution_cases.json").read_bytes())["questions"]
POSITIVE = json.loads((BACKEND / "tests/fixtures/execution_positive.json").read_bytes())["cases"]
SMOKE = json.loads((BACKEND / "tests/fixtures/execution_smoke.json").read_bytes())["cases"]
KEYS = ("prep-remove-all-ascii-spaces", "prep-cursor-list-using-two-stacks",
        "prep-fifo-queue-using-two-stacks")
CASES = [(key, case) for key in KEYS for case in MANIFEST[key]["languages"]["python"]["cases"]]


def reference(key):
    row = next(item for item in POSITIVE if item["question_key"] == key)
    namespace = {}
    exec(compile(row["source"], "<trusted-Nov8-reference>", "exec"), namespace)
    return namespace[MANIFEST[key]["languages"]["python"]["entry"]]


@pytest.mark.parametrize("key", KEYS)
def test_input_only_cases_and_independent_expected_values(key):
    assert set(INPUTS) == set(AUTHORING["BATCH1108B20_ORACLES"]) == set(KEYS)
    given = INPUTS[key]["languages"]["python"]
    built = MANIFEST[key]["languages"]["python"]
    assert len(given["cases"]) == len(built["cases"]) == 12
    assert all(set(case) == {"args"} for case in given["cases"])
    assert [case["args"] for case in built["cases"]] == [case["args"] for case in given["cases"]]
    oracle = AUTHORING["BATCH1108B20_ORACLES"][key]
    assert all(case["expected"] == oracle(*case["args"]) for case in built["cases"])


@pytest.mark.parametrize("key,case", CASES)
def test_trusted_algorithm_matches_case_and_preserves_input(key, case):
    args = copy.deepcopy(case["args"])
    assert reference(key)(*args) == case["expected"]
    assert args == case["args"]


@pytest.mark.parametrize("key", KEYS)
def test_wrong_and_syntax_developer_fixtures_fail(key):
    row = next(item for item in SMOKE if item["question_key"] == key)
    with pytest.raises(SyntaxError):
        compile(row["syntax_error"], "<invalid-Nov8-fixture>", "exec")
    namespace = {}
    exec(compile(row["wrong"], "<wrong-Nov8-fixture>", "exec"), namespace)
    candidate = namespace[MANIFEST[key]["languages"]["python"]["entry"]]
    assert any(candidate(*copy.deepcopy(case["args"])) != case["expected"]
               for case in MANIFEST[key]["languages"]["python"]["cases"])


def test_ascii_space_contract_and_invalid_transcripts():
    remove = reference(KEYS[0])
    assert remove(" a\t b\n\u00a0 ") == "a\tb\n\u00a0"
    with pytest.raises(TypeError):
        remove(None)
    for key in KEYS[1:]:
        with pytest.raises(ValueError):
            reference(key)([["unknown"]])
        with pytest.raises(ValueError):
            reference(key)([["enqueue", 1, 2]])


def test_cursor_class_uses_constant_local_stack_work_and_excludes_other_native_models():
    tree = ast.parse(AUTHORING["batch1108b20_source"](KEYS[1]))
    cursor = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "CursorList")
    assert not any(isinstance(node, (ast.For, ast.While, ast.ListComp, ast.DictComp, ast.SetComp))
                   for node in ast.walk(cursor))
    assert "prep-java-fixed-capacity-integer-stack" not in MANIFEST
    assert "prep-exact-integer-division-unit-instructions" not in MANIFEST
    for key in KEYS:
        assert len([row for row in POSITIVE if row["question_key"] == key]) == 1
        assert len([row for row in SMOKE if row["question_key"] == key]) == 1
