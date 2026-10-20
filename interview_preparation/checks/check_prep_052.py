"""Check the five-MUX full-adder netlist against integer addition."""
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prep052", ROOT / "solutions/prep_052_full_adder_mux.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
available = {"A", "B", "Cin", "0", "1"}
for out, select, d0, d1 in model.NETLIST:
    assert out not in available
    assert {select, d0, d1} <= available
    available.add(out)
assert len(model.NETLIST) == 5
zero_available = {"A", "B", "Cin", "0"}
for out, select, d0, d1 in model.ZERO_ONLY_NETLIST:
    assert out not in zero_available
    assert {select, d0, d1} <= zero_available
    zero_available.add(out)
assert len(model.ZERO_ONLY_NETLIST) == 5
rows = []
for A, B, Cin in itertools.product((0, 1), repeat=3):
    S, Cout = model.full_adder(A, B, Cin)
    assert (S, Cout) == ((A + B + Cin) % 2, (A + B + Cin) // 2)
    assert S + 2 * Cout == A + B + Cin
    assert model.full_adder(A, B, Cin, zero_only=True) == (S, Cout)
    rows.append([A, B, Cin, S, Cout])
report = {
    "question_id": "PREP-052", "status": "passed", "checked_on": "2026-10-20",
    "exhaustive_truth_rows": len(rows), "mux_instances": len(model.NETLIST),
    "zero_only_alternative_truth_rows": len(rows), "zero_only_mux_instances": len(model.ZERO_ONLY_NETLIST),
    "topological_netlist_valid": True, "external_constants": [0, 1],
    "complements_generated_by_mux": ["nB", "nCin"],
    "truth_rows_A_B_Cin_S_Cout": rows,
    "limitations": "Five-MUX sufficiency with constants 0/1, no global minimum claim. Python model only, not HDL compilation/simulation or timing.",
}
(ROOT / "checks/prep-052-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
