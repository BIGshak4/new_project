"""All 256 input words; independent multiplication and weighted-FA invariants."""
import itertools
import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_100_times_six_full_adders import full_adder, times_six

for a, b, c in itertools.product((0, 1), repeat=3):
    s, k = full_adder(a, b, c)
    assert s + 2 * k == sum((a, b, c))
for value in range(256):
    result, rows = times_six(value, with_trace=True)
    assert result == 6 * value and 0 <= result <= 1530
    assert len(rows) == 8 and result & 1 == 0
    assert ((result >> 1) & 1) == value & 1
    assert [row["column"] for row in rows] == list(range(2, 10))
    for row in rows:
        assert row["a"] + row["b"] + row["carry_in"] == row["sum"] + 2 * row["carry_out"]
    # Separate decimal arithmetic oracle and bit-position reconstruction.
    assert int(f"{result:011b}", 2) == sum(value for _ in range(6))
assert times_six(255) == 1530 and times_six(0) == 0
for bad in (-1, 256, True, None, 1.5):
    try:
        times_six(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid input accepted")
record = {
    "question_id": "PREP-100", "checked_on": "2026-10-24", "status": "passed",
    "full_adder_truth_rows": 8, "exhaustive_unsigned_inputs": 256,
    "weighted_column_checks": 2048, "full_adders_per_input": 8,
    "oracle": "Exact integer multiplication plus independent repeated addition; weighted-column conservation.",
    "scope": "Unsigned 8-bit input, exact 11-bit output; Python logical steady-state model only. No minimum-FA proof, HDL compilation, synthesis or physical timing verification.",
}
(BANK / "checks/prep-100-verification.json").write_text(
    json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record))
