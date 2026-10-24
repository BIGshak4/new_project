"""Independent integer oracles and complete two-gate library enumeration."""
from __future__ import annotations

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
    cmp = load("prep_110_unsigned_comparator")
    gates = load("prep_112_and_from_inverted_input_gates")
    comparisons = 0
    for width in range(1, 7):
        for a, b in itertools.product(range(1 << width), repeat=2):
            got = cmp.compare_words(a, b, width)
            assert got == (int(a > b), int(a == b), int(a < b))
            assert sum(got) == 1
            comparisons += 1
    for a, b in itertools.product((0, 1), repeat=2):
        assert cmp.compare_bit(a, b) == (int(a > b), int(a == b), int(a < b))
        expected = int(a == 1 and b == 1)
        assert gates.both_with_zero(a, b) == expected
        assert gates.no_constants(a, b) == expected
        assert gates.both_no_constants(a, b) == expected
    # Four truth rows 00,01,10,11; A=1100,B=1010,Y=1000.
    mask, target = 15, 8
    functions = {"F": lambda a, b: a & (~b & mask),
                 "G": lambda a, b: a | (~b & mask)}
    primary = [12, 10]
    one_gate = {fn(a, b) for fn in functions.values()
                for a, b in itertools.product(primary + [0], repeat=2)}
    assert target not in one_gate
    mixed_no_constant = set()
    networks = 0
    for first, second in (("F", "G"), ("G", "F")):
        for a, b in itertools.product(primary, repeat=2):
            t = functions[first](a, b)
            for c, d in itertools.product(primary + [t], repeat=2):
                mixed_no_constant.add(functions[second](c, d))
                networks += 1
    assert networks == 72 and target not in mixed_no_constant
    return {"status": "passed", "comparator_word_pairs_widths_1_to_6": comparisons,
            "four_bit_pairs": 256, "one_bit_rows": 4,
            "and_constructions_rows": 12,
            "two_gate_mixed_no_constant_networks": networks,
            "scope": "Executed two-state Python gate models, not HDL or physical timing."}


if __name__ == "__main__":
    result = verify()
    for number in (110, 112):
        (ROOT / "checks" / f"prep-{number:03d}-verification.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
