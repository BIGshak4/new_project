"""Check all inputs and enforce the constant-zero-only MUX library."""
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prep051", ROOT / "solutions/prep_051_xor_three_mux_zero.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
available = {"A", "B", "C", "0"}
for out, select, d0, d1 in model.NETLIST:
    assert out not in available
    assert {select, d0, d1} <= available
    available.add(out)
assert len(model.NETLIST) == 4
rows = []
for A, B, C in itertools.product((0, 1), repeat=3):
    actual = model.xor_three(A, B, C)
    expected = (A + B + C) % 2
    assert actual == expected
    # Separate conditional reasoning for two-input block, not XOR operator reuse.
    for X, Y in ((A, B), (actual, C)):
        t = model.mux(Y, X, 0)
        assert model.mux(X, Y, t) == (X + Y) % 2
    rows.append([A, B, C, actual])
report = {
    "question_id": "PREP-051", "status": "passed", "checked_on": "2026-10-20",
    "exhaustive_truth_rows": len(rows), "mux_instances": len(model.NETLIST),
    "topological_netlist_valid": True, "only_external_constant": 0,
    "truth_rows_A_B_C_F": rows,
    "limitations": "Four-MUX sufficiency only; no minimum claim. Python model, no HDL compilation/simulation or physical timing.",
}
(ROOT / "checks/prep-051-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
