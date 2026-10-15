"""Learner copy must stay paired, preserve source/review boundaries, and contain usable examples."""
import ast
import bisect
import importlib.util
import json
import re
from itertools import product
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def builder():
    spec = importlib.util.spec_from_file_location("wording_builder", ROOT / "backend/scripts/build_preparation_bank.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("overrides", [
    {"he": {"prompt": "text"}},
    {"he": {"prompt": "text"}, "en": {"reference_solution": "answer"}},
    {"he": {"status": "published"}, "en": {"status": "published"}},
    {"he": {"prompt": ""}, "en": {"prompt": "text"}},
    {"he": {"prompt": 7}, "en": {"prompt": "text"}},
])
def test_website_copy_rejects_unpaired_empty_or_review_edits(overrides):
    with pytest.raises(ValueError):
        builder().learner_text({"learner_text": overrides}, "PREP-001")


def test_prepared_copy_keeps_source_and_study_only_status():
    compiled, _ = builder().load()
    for row in compiled:
        assert row["status"] == "trial" and row["reviewed_by"] is None
        assert row["assets"]["assessment_ready"] is False
        material = row["assets"]["preparation_resource"]
        assert material["website_editorial"]["human_review_pending"] is True
        for lang in ("he", "en"):
            assert material["translations"][lang]["prompt"] == row["translations"][lang]["prompt"]
    by_key = {q["key"]: q for q in compiled}
    waveform = by_key["prep-circuit-from-clock-input-output-waveforms"]
    assert "| 0 | 0 | 1 | 1 | 1 | 1 | 0 | 0 |" in waveform["translations"]["he"]["prompt"]
    timing = by_key["prep-critical-path-mux-multiplier"]
    assert "R = MUX(NOT(S), A, B)" in timing["translations"]["he"]["prompt"]
    assert timing["assets"]["reported_companies"]


def test_displayed_positive_divisibility_tables_match_every_short_binary_input():
    compiled, _ = builder().load()
    fsm = next(q for q in compiled if q["key"] == "prep-serial-binary-divisibility-by-three-fsm")
    for lang in ("he", "en"):
        rows = re.findall(r"^\| (Z|R[012]) \| (Z|R[012]) \| (Z|R[012]) \| ([01]) \|$",
                          fsm["translations"][lang]["reference_solution"], re.M)
        table = {state: (zero, one, int(output)) for state, zero, one, output in rows}
        assert len(table) == 4
        for length in range(11):
            for bits in product((0, 1), repeat=length):
                state, value = "Z", 0
                for bit in bits:
                    state = table[state][bit]
                    value = 2 * value + bit
                    assert table[state][2] == int(value > 0 and value % 3 == 0)


def example_snippets():
    data = json.loads((ROOT / "example_question/questions.json").read_text(encoding="utf-8"))
    found = {}
    for row in data["questions"]:
        for lang in ("he", "en"):
            for snippet in re.findall(r"```python\n(.*?)\n```", row["translations"][lang]["reference_solution"], re.S):
                ast.parse(snippet)
                found[row["key"]] = snippet
    return found


def test_published_example_snippets_match_independent_small_oracles():
    # These are trusted, repository-authored reference snippets, not candidate code.
    snippets = example_snippets()
    functions = {}
    for snippet in snippets.values():
        exec(compile(snippet, "reference_solution", "exec"), functions)
    count = functions["count_set_bits"]
    for value in list(range(1024)) + [0xFFFFFFFF, 0x80000000]:
        assert count(value) == bin(value).count("1")
    lower = functions["lower_bound"]
    for values in [[], [2], [2, 4, 4, 9], [-3, -3, 0, 8]]:
        for target in range(-4, 12):
            assert lower(values, target) == bisect.bisect_left(values, target)
    pair = functions["pair_sum_indices"]
    for values in [[], [6], [6, 6], [3, -2, 7, 3], [0, 0, 1]]:
        for target in range(-5, 16):
            possible = [(i, j) for i in range(len(values)) for j in range(i+1, len(values))
                        if values[i] + values[j] == target]
            actual = pair(values, target)
            assert (actual is not None) == bool(possible)
            if actual:
                i, j = actual
                assert i != j and values[i] + values[j] == target
    brackets = functions["valid_brackets"]
    for value, expected in [("", True), ("([]{})", True), ("([)]", False), ("]", False), ("((", False)]:
        assert brackets(value) is expected
