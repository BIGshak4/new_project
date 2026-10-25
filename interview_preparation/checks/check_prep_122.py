"""Independent arithmetic and column invariants for the HA-only circuit."""
import importlib.util
import itertools
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("half_only", BANK / "solutions/prep_122_half_adder_only.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    primitive = pairs = columns = exclusion = 0
    for a, b in itertools.product((0, 1), repeat=2):
        s, carry = model.half_adder(a, b)
        assert s == (a + b) % 2 and carry == (a + b) // 2
        primitive += 1
    for a, b in itertools.product(range(16), repeat=2):
        assert model.add4(a, b) == a + b
        rows = model.trace_add4(a, b)
        assert sum(row["ha_cells"] for row in rows) == 10
        incoming = 0
        for bit, row in enumerate(rows):
            assert row["cin"] == incoming
            assert row["a"] + row["b"] + incoming == row["sum"] + 2 * row["cout"]
            incoming = row["cout"]
            if bit:
                assert row["g"] + row["h"] in (0, 1)
                assert row["cout"] == row["g"] + row["h"]
                assert row["discarded"] == 0
                exclusion += 1
            columns += 1
        pairs += 1
    rejected = 0
    for a, b in ((-1, 0), (16, 0), (0, 16), (True, 0), (1.5, 2)):
        try:
            model.add4(a, b)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError((a, b))
    return {"question_id": "PREP-122", "status": "passed", "ha_primitive_rows": primitive,
            "operand_pairs": pairs, "weighted_column_checks": columns,
            "exclusive_carry_and_zero_discard_checks": exclusion,
            "ha_cells_in_construction": 10, "invalid_inputs_rejected": rejected,
            "scope": "Exhaustive fixed-width Python Boolean model versus ordinary integer addition and column invariants. Ten HA is a construction, not a minimum. No HDL compilation, synthesis or physical timing/power/area validation; human professional review pending."}


if __name__ == "__main__":
    evidence = run_checks()
    (BANK / "checks/prep-122-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))
