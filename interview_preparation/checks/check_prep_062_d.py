"""Marker-only variant D: verify all integer distances against an independent schedule."""

import importlib.util
import inspect
import json
import sys
from fractions import Fraction
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("flags_d", BANK / "solutions/prep_062_d_flags_no_meeting_sensor.py")
model = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = model
spec.loader.exec_module(model)


def analytic_position(start, tick, *, trailer=False, distance=1):
    # Direct cumulative action counts, independent of the authored state machine.
    if not trailer or tick <= 2 * distance - 1:
        return start + (tick + 1) // 2
    return start + distance + tick - (2 * distance - 1)


def run_checks():
    checked, trajectory_points = 0, 0
    for distance in range(1, 129):
        for origin in (-1000, 0, 37):
            for swapped in (False, True):
                result = model.simulate(distance, origin=origin, swapped=swapped)
                assert result["first_meeting"] == 4 * distance - 2
                for tick, positions in enumerate(result["trajectory"]):
                    expected = [analytic_position(origin, tick, trailer=True, distance=distance),
                                analytic_position(origin + distance, tick)]
                    if swapped:
                        expected.reverse()
                    assert positions == expected
                    trajectory_points += 1
                assert all(action in {"right", "wait"}
                           for pair in result["actions"] for action in pair)
                checked += 1
    for d in (129, 255, 512, 1024):
        assert model.simulate(d)["first_meeting"] == 4 * d - 2
        checked += 1
    # A physical meeting does not cause either local controller to stop.
    zero = model.simulate(0, max_ticks=10)
    assert zero["first_meeting"] == 0
    assert all(left == right for left, right in zero["trajectory"])
    assert zero["actions"]
    counterexamples = 0
    for distance in (Fraction(1, 2), Fraction(3, 2), Fraction(17, 2)):
        assert model.simulate(distance, max_ticks=100)["first_meeting"] is None
        counterexamples += 1
    assert list(inspect.signature(model.FlagProgram.command).parameters) == ["self", "flag_here"]
    program = model.FlagProgram()
    assert [program.command(flag) for flag in (True, False, False, True, False)] == [
        "right", "wait", "right", "right", "right",
    ]
    return {
        "question_id": "PREP-062", "variant": "D_marker_only_no_meeting_sensor",
        "status": "passed", "integer_distance_cases": checked,
        "trajectory_points_vs_independent_formula": trajectory_points,
        "zero_separation": "co-located initially; programs continue timed actions",
        "half_integer_counterexamples": counterexamples,
        "local_sensor_inputs": ["flag_here"],
        "scope": "Synchronized start, shared direction, integer separation, unit movement/wait, free control/query. Harness alone observes physical meeting; no automatic stop or minimum-time claim.",
    }


if __name__ == "__main__":
    evidence = run_checks()
    (BANK / "checks/prep-062-d-verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))
