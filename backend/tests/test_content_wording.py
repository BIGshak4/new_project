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


@pytest.mark.parametrize("hints", [
    {"he": ["one", "two", "three"]},
    {"he": ["one"], "en": ["one", "two", "three"]},
    {"he": ["one", "two", ""], "en": ["one", "two", "three"]},
    {"he": ["one", "two", 3], "en": ["one", "two", "three"]},
])
def test_learner_hint_edits_require_three_nonempty_paired_hints(hints):
    with pytest.raises(ValueError):
        builder().learner_hints({"learner_hints": hints}, "PREP-110")


@pytest.mark.parametrize("overrides", [
    {"status": {"he": "published", "en": "published"}},
    {"id": {"he": "other", "en": "other"}},
    {"reviewed_by": {"he": "person", "en": "person"}},
    {"assumptions": {"he": "text"}},
    {"assumptions": {"he": "different", "en": "text"}},
])
def test_download_copy_edits_cannot_change_identity_review_or_display_parity(overrides):
    displayed = {"assumptions": {"he": "text", "en": "text"}}
    with pytest.raises(ValueError):
        builder().learner_resource_fields({"learner_resource_fields": overrides}, "PREP-110", displayed)


def test_learner_caption_edits_cannot_add_paths_or_expose_archived_images():
    module = builder()
    question = {"id": "PREP-110", "media_assets": [{"path": "diagrams/existing.png"}]}
    for captions in ({"sources/original.png": "source"}, {"diagrams/other.png": "new"},
                     {"diagrams/existing.png": ""}):
        with pytest.raises(ValueError):
            module.apply_learner_media_captions(question, {"learner_media_captions": captions})


def test_prep110_cleans_display_and_download_without_rewriting_source_or_review():
    module = builder()
    raw = next(q for q in json.loads((module.BANK / "questions.json").read_bytes())["questions"]
               if q["id"] == "PREP-110")
    rows, _ = module.load()
    row = next(q for q in rows if q["assets"]["preparation_id"] == "PREP-110")
    assert "צילום 14" in raw["translations"]["he"]["prompt"]
    assert raw["key"] == row["key"].removeprefix("prep-")
    assert raw["version"] == row["version"]
    assert row["status"] == "trial" and row["reviewed_by"] is None
    assert not row["assets"]["assessment_ready"]
    resource = row["assets"]["preparation_resource"]
    retired = re.compile(r"צילום\s*14|screenshot[- ]fourteen|editorial completion|השלמה עריכתית|"
                         r"לפי בקשה מפורשת של המשתמש|at the user's explicit request|truncated", re.I)
    assert not retired.search(json.dumps(row, ensure_ascii=False))
    for language in ("he", "en"):
        text = row["translations"][language]
        assert len(text["hints"]) == 3
        assert resource["translations"][language]["hint"] == text["hints"][0]
        assert resource["translations"][language]["hints"] == text["hints"]
        assert "X=(A>B)" in text["prompt"] and "Y=(A<B)" in text["prompt"]
    for field, paired in resource["learner_material"].items():
        assert resource[field] == paired
    # The authorized copy edit must retain the actual four-row circuit exercise.
    for language in ("he", "en"):
        solution = row["translations"][language]["reference_solution"]
        assert "X=A AND NOT B" in solution and "Y=NOT A AND B" in solution
        assert "|0|0|0|0|" in solution and "|1|1|0|0|" in solution


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
