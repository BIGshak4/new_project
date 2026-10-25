"""Ripple cells checked against multiplication/repeated-addition oracles."""
import importlib.util
import itertools
import json
import random
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("times134", BANK / "solutions/prep_134_constant_times_thirteen.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    primitive = cases = columns = 0
    for a, b, c in itertools.product((0, 1), repeat=3):
        s, carry = model.full_adder(a, b, c)
        assert a + b + c == s + 2 * carry
        primitive += 1
    inputs = [(n, x) for n in range(1, 11) for x in range(1 << n)]
    rng = random.Random(134)
    inputs += [(n, rng.getrandbits(n)) for n in (16, 32, 65, 127) for _ in range(100)]
    for width, value in inputs:
        result, first, second = model.times_thirteen(value, width, with_trace=True)
        assert result == value * 13 == sum(value for _ in range(13))
        assert result < (1 << (width + 4))
        for trace in (first, second):
            previous = 0
            for a, b, carry, s, following in trace:
                assert carry == previous
                assert a + b + carry == s + 2 * following
                previous = following
                columns += 1
            assert previous == 0
        cases += 1
    rejected = 0
    for value, width in ((0, 0), (0, True), (-1, 4), (16, 4), (True, 4)):
        try:
            model.times_thirteen(value, width)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError((value, width))
    return {"question_id": "PREP-134", "status": "passed", "fa_truth_rows": primitive,
            "exhaustive_cases_widths_one_through_ten": 2046, "seeded_wide_cases": 400,
            "product_cases": cases, "weighted_column_checks": columns, "invalid_inputs_rejected": rejected,
            "scope": "Executed padded two-ripple-adder Python model, independent integer multiplication/repeated addition and per-cell conservation. No minimum-adder proof, HDL, synthesis or measured timing; human review pending."}


if __name__ == "__main__":
    evidence = run_checks()
    (BANK / "checks/prep-134-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))
