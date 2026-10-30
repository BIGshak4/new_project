"""Independent crossing, arrival-window and charge checks for teaching models."""

import importlib.util
import itertools
import json
import math
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / "solutions" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_checks():
    buffer = load("prep_175_buffer_load_model")
    timing = load("prep_176_setup_hold_budgets")
    coupling = load("prep_177_capacitive_crosstalk")
    counts = {175: 0, 176: 0, 177: 0}
    for r, c, threshold in itertools.product((1, 10, 1000), (1e-12, 1e-11, 1e-9), (0.1, 0.5, 0.9)):
        # Independently bracket the crossing of the exponential response.
        lo, hi = 0.0, 10 * r * c
        for _ in range(80):
            mid = (lo + hi) / 2
            if 1 - math.exp(-mid / (r * c)) < threshold:
                lo = mid
            else:
                hi = mid
        assert math.isclose(buffer.rc_crossing(r, c, threshold), (lo + hi) / 2, rel_tol=1e-12)
        counts[175] += 1
    direct, buffered = buffer.compare_paths(1000, 100e-12, 2e-12, 50, 1e-9)
    assert buffered < direct
    direct, buffered = buffer.compare_paths(1000, 0.1e-12, 2e-12, 50, 1e-9)
    assert buffered > direct
    counts[175] += 2
    for period, logic_min, logic_max, skew in itertools.product(
        (1, 2, 4), (0.05, 0.2), (0.5, 1.7, 3.2), (-0.2, 0, 0.2)
    ):
        got = timing.timing_slacks(period, 0.08, 0.2, logic_min, logic_max, 0.15, 0.1, skew, 0.03, 0.02)
        # Absolute times: launch edge at7; capture edge at7+skew.
        latest = 7 + 0.2 + logic_max
        deadline = 7 + period + skew - 0.15 - 0.03
        earliest = 7 + 0.08 + logic_min
        hold_until = 7 + skew + 0.1 + 0.02
        assert math.isclose(got[0], deadline - latest, abs_tol=1e-12)
        assert math.isclose(got[1], earliest - hold_until, abs_tol=1e-12)
        slower = timing.timing_slacks(
            period + 1, 0.08, 0.2, logic_min, logic_max, 0.15, 0.1, skew, 0.03, 0.02
        )
        assert math.isclose(slower[0] - got[0], 1) and slower[1] == got[1]
        counts[176] += 1
    for cg, cc, ratio in itertools.product((1.0, 3.0, 10.0), (0.0, 0.2, 2.0), (-1, 0, 1)):
        # Charge on each capacitor from start/end voltages, not delay formula.
        dv, da = 0.8, ratio * 0.8
        q_ground = cg * dv
        q_coupling = cc * (dv - da)
        assert math.isclose(coupling.effective_capacitance(cg, cc, ratio) * dv, q_ground + q_coupling)
        counts[177] += 1
    for cg, cc in itertools.product((1.0, 5.0), (0.0, 1.0, 10.0)):
        delays = [coupling.illustrative_delay(10, cg, cc, ratio) for ratio in (1, 0, -1)]
        assert delays[0] <= delays[1] <= delays[2]
        counts[177] += 1
    rejected = [
        lambda: buffer.rc_crossing(0, 1),
        lambda: buffer.rc_crossing(1, -1),
        lambda: buffer.rc_crossing(1, 1, 1),
        lambda: timing.timing_slacks(1, 0.2, 0.1, 0, 0, 0, 0),
        lambda: coupling.effective_capacitance(1, 1, 2),
    ]
    for bad in rejected:
        try:
            bad()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid parameters accepted")
    for number, count in counts.items():
        result = {
            "question_id": f"PREP-{number}",
            "status": "passed",
            "independent_cases": count,
            "scope": "Python mathematical teaching model; no synthesis, SPICE, extracted parasitics, STA signoff or physical measurements.",
        }
        (BANK / f"checks/prep-{number}-verification.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
    return {"case_counts": counts, "rejected_invalid_parameters": len(rejected)}


if __name__ == "__main__":
    print(json.dumps(run_checks()))
