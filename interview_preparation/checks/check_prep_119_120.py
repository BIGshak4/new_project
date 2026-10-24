"""Actual code checked with independent arithmetic and Boolean truth oracles."""
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "solutions" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify():
    toggle = load("prep_119_toggle_nine_thirteen")
    gates = load("prep_120_nand_nor_mux")
    assert [toggle.toggle_nine_thirteen(x) for x in (9, 13)] == [13, 9]
    for first, second in itertools.product(range(256), repeat=2):
        assert toggle.toggle_pair(first, first, second) == second
        assert toggle.toggle_pair(second, first, second) == first
    rows = tuple(itertools.product((0, 1), repeat=2))
    for a, b in rows:
        assert gates.nand_nor(a, b) == (int(not (a and b)), int(not (a or b)))
    vectors = [(0, 0, 1, 1), (0, 1, 0, 1), (0, 0, 0, 0), (1, 1, 1, 1)]
    functions = set()
    for select, data0, data1 in itertools.product(vectors, repeat=3):
        result = tuple(gates.mux(s, z, o) for s, z, o in zip(select, data0, data1, strict=True))
        functions.add(result)
    target_nand, target_nor = (1, 1, 1, 0), (1, 0, 0, 0)
    assert target_nand not in functions and target_nor not in functions
    return {"status": "passed", "swap_domain_cases": 2,
            "generalized_byte_pair_cases": 65536, "generalized_direction_checks": 131072,
            "nand_nor_truth_rows": 4, "single_mux_wiring_choices_exhausted": 64,
            "different_single_mux_functions": len(functions),
            "scope": "Executed Python binary models; finite gate-library proof, no HDL or physical circuit test."}


if __name__ == "__main__":
    result = verify()
    for number in (119, 120):
        (ROOT / "checks" / f"prep-{number}-verification.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
