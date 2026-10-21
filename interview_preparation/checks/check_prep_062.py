"""Interpreter checks with an independent closed-form meeting-time oracle."""
import importlib.util
import json
from fractions import Fraction
from pathlib import Path
import sys

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rendezvous", BANK / "solutions/prep_062_identical_agents.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def run():
    cases = 0
    offsets = (-1000, 0, 37)
    for distance in range(1, 257):
        for sign in (-1, 1):
            for offset in offsets:
                result = module.simulate(sign * distance, offset=offset)
                assert result["met"]
                assert result["time"] == 6 * distance - 1, (distance, result)
                rear = 0 if sign > 0 else 1
                assert result["marker_hits"] == [(rear, 3 * distance - 1)]
                cases += 1
    assert module.simulate(0)["time"] == 0
    # Two explicit limits: sampled point markers can be missed, and agents
    # heading away from each other do not satisfy common-forward orientation.
    misses = 0
    for numerator in (1, 3, 7, 21):
        d = Fraction(numerator, 2)
        result = module.simulate(d, max_ticks=300)
        assert not result["met"] and not result["marker_hits"]
        misses += 1
    assert not module.simulate(5, directions=(-1, 1), max_ticks=300)["met"]
    # Local actions depend only on PC + one marker bit, never hidden position.
    assert set(module.LocalCPU.__dataclass_fields__) == {"pc"}
    assert module.PROGRAM_TEXT.count("MF") == 3 and "ELSE" not in module.PROGRAM_TEXT
    result = {
        "question_id": "PREP-062", "status": "passed",
        "integer_interpreter_runs": cases, "tested_distances": "1..256, both agent orders, three translations",
        "independent_time_formula": "6*abs(D)-1 ticks; marker test at3*abs(D)-1",
        "zero_distance": "already met",
        "noninteger_marker_miss_counterexamples": misses,
        "opposite_forward_direction_counterexample": True,
        "primitive_cost_model": "Every executed MF, ifP test and GOTO costs one tick. A false ifP skips its guarded GOTO. Collision is checked continuously inside each move interval, not only at the end.",
        "limits": "Finite interpreter tests support a separate all-positive-integer proof; not hardware, asynchronous-start or arbitrary-orientation verification. The CPU only receives a local marker bit and stores its program counter.",
    }
    (BANK / "checks/prep-062-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
