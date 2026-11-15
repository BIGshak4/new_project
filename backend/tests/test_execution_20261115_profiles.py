"""Input-only Nov 15 cases use independent oracles and trusted reference sources."""
import copy
import json
import runpy
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
AUTHORING = runpy.run_path(str(BACKEND / "tests/fixtures/execution_catalog_authoring.py"))
INPUTS = json.loads((BACKEND / "tests/fixtures/execution_batch1115_inputs.json").read_bytes())
MANIFEST = json.loads((BACKEND / "seeds/execution_cases.json").read_bytes())["questions"]
KEYS = ("prep-interesting-digital-clock-times", "prep-binary-tree-preorder-null-codec")


@pytest.mark.parametrize("key", KEYS)
def test_input_only_cases_are_derived_by_independent_oracles(key):
    given = INPUTS[key]["languages"]["python"]
    actual = MANIFEST[key]["languages"]["python"]
    assert len(given["cases"]) == len(actual["cases"]) == 12
    assert all(set(case) == {"args"} for case in given["cases"])
    namespace = {}
    exec(compile(AUTHORING["batch1115_source"](key), key, "exec"), namespace)
    reference = namespace[actual["entry"]]
    for source, case in zip(given["cases"], actual["cases"], strict=True):
        assert source["args"] == case["args"]
        expected = AUTHORING["ORACLES"][key](*copy.deepcopy(source["args"]))
        assert expected == case["expected"]
        assert reference(*copy.deepcopy(case["args"])) == expected


def test_tree_profile_preserves_shapes_that_share_preorder_values():
    namespace = {}
    exec(AUTHORING["batch1115_source"](KEYS[1]), namespace)
    round_trip = namespace["tree_codec_round_trip"]
    assert round_trip("[7,7,null,null,null]") != round_trip("[7,null,7,null,null]")
    with pytest.raises(ValueError):
        round_trip("[7,null]")
    with pytest.raises(ValueError):
        round_trip("[null,null]")
