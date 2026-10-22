"""Exhaustive and deterministic random checks against independent bit_length."""
import itertools
import json
import random
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_086_highest_onehot_tree import (
    abstract_bounds,
    balanced,
    cell2,
    serial,
)


def oracle(value):
    return 0 if value == 0 else 1 << (value.bit_length() - 1)


def check(value, width):
    expected = oracle(value)
    for method in (serial, balanced):
        result = method(value, width)
        assert result == expected
        assert result & value == result
        assert result == 0 or result & (result - 1) == 0
    return 2


def main():
    rows = 0
    for high, low, blocked in itertools.product(range(2), repeat=3):
        valid, gh, gl = cell2(high, low, blocked)
        assert valid == int(bool(high or low))
        expected = 0 if blocked else oracle(2 * high + low)
        assert 2 * gh + gl == expected
        rows += 1
    exhaustive = comparisons = 0
    for width in range(1, 14):
        for value in range(1 << width):
            comparisons += check(value, width)
            exhaustive += 1
    random_cases = 0
    randomizer = random.Random(20261022)
    widths = [1, 2, 3, 5, 7, 8, 9, 15, 16, 17, 31, 33, 63, 64, 65, 127, 257]
    for width in widths:
        for _ in range(100):
            comparisons += check(randomizer.getrandbits(width), width)
            random_cases += 1
        for bit in range(width):
            comparisons += check(1 << bit, width)
    for width in range(1, 258):
        bounds = abstract_bounds(width)
        assert width <= bounds["padded_width"] < 2 * width
        assert bounds["balanced_gate_upper"] < 8 * width
    rejected = 0
    for value, width in ((0, 0), (-1, 3), (8, 3)):
        for method in (serial, balanced):
            try:
                method(value, width)
            except ValueError:
                rejected += 1
            else:
                raise AssertionError("invalid input accepted")
    result = {"question_id": "PREP-086", "status": "passed", "base_unit_truth_rows": rows,
              "exhaustive_widths": [1, 13], "exhaustive_vectors": exhaustive,
              "random_vectors": random_cases, "maximum_random_width": 257,
              "implementation_comparisons": comparisons, "invalid_inputs_rejected": rejected,
              "scope": "Python functional models and symbolic topology bounds only; no HDL, synthesis, measured propagation timing or hardware verification",
              "professional_review": "pending"}
    (BANK / "checks/prep-086-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
