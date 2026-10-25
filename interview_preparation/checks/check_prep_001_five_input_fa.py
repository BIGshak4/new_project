"""Exhaust inputs and all acyclic FA networks of size at most two."""
import importlib.util
import itertools
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("five_fa", BANK / "solutions/prep_001_five_input_fa.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def primitive_words(a, b, c):
    # Independent count-of-inputs definition, rather than copying XOR/majority.
    totals = [((a >> row) & 1) + ((b >> row) & 1) + ((c >> row) & 1) for row in range(32)]
    return tuple(sum(((count >> bit) & 1) << row for row, count in enumerate(totals)) for bit in (0, 1))


def run_checks():
    primitive = columns = 0
    for a, b, c in itertools.product((0, 1), repeat=3):
        s, carry = model.full_adder(a, b, c)
        assert s + 2 * carry == a + b + c
        primitive += 1
    for value in range(32):
        wires = model.network(value)
        assert model.popcount5(value) == sum(map(int, f"{value:05b}"))
        x = wires["x"]
        assert sum(x[:3]) == wires["s1"] + 2 * wires["c1"]
        assert wires["s1"] + x[3] + x[4] == wires["y0"] + 2 * wires["c2"]
        assert wires["c1"] + wires["c2"] == wires["y1"] + 2 * wires["y2"]
        columns += 3
    # Every 0/1/2-cell DAG has a topological order. Inputs are the five raw
    # truth words plus free zero, followed by both outputs of previous cells.
    # Repeated pins/fanout are allowed, and any available wire may be an output.
    raw = [sum(((row >> bit) & 1) << row for row in range(32)) for bit in range(5)] + [0]
    targets = [sum(((sum(map(int, f"{row:05b}")) >> bit) & 1) << row for row in range(32)) for bit in range(3)]
    assert not all(target in raw for target in targets)
    one = two = 0
    for first in itertools.combinations_with_replacement(range(6), 3):
        wires = raw + list(primitive_words(*(raw[index] for index in first)))
        assert not all(target in wires for target in targets)
        one += 1
        for second in itertools.combinations_with_replacement(range(8), 3):
            final = wires + list(primitive_words(*(wires[index] for index in second)))
            assert not all(target in final for target in targets)
            two += 1
    rejected = 0
    for value in (-1, 32, True, 1.5):
        try:
            model.popcount5(value)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(value)
    return {"question_id": "PREP-001", "variant": "five_input_fa_only", "status": "passed",
            "fa_primitive_rows": primitive, "input_vectors": 32, "weighted_column_checks": columns,
            "zero_cell_networks_excluded": 1, "one_cell_networks_excluded": one,
            "two_cell_networks_excluded": two, "invalid_inputs_rejected": rejected,
            "minimum_fa_count_under_declared_model": 3,
            "scope": "Complete finite Boolean enumeration: three-input FA cells, raw inputs/free zero, arbitrary repeated pins/fanout, acyclic wiring and direct output taps. No extra logic/complements/constants. Python only, not HDL, physical timing, area or power proof; human review pending."}


if __name__ == "__main__":
    evidence = run_checks()
    (BANK / "checks/prep-001-five-input-fa-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))
