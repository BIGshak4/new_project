"""Finite recurrence compared with independent integer multiplication."""

import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("square140", BANK / "solutions/prep_140_cycle_and_square.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    steps = reset_cases = 0
    for limit in range(257):
        wn, ws = model.widths(limit)
        for cycle, (n, square) in enumerate(model.trace(limit, limit + 3)):
            expected = min(cycle, limit)
            assert n == expected and square == expected**2
            assert n < 1 << wn and square < 1 << ws
            assert model.step(n, square, limit, reset=True) == (0, 0)
            steps += 1
            reset_cases += 1
    wide = 0
    for limit in (65535, 2**32, 2**64 - 1):
        for n in (0, 1, limit // 2, limit - 1, limit):
            a, b = model.step(n, n * n, limit)
            assert a == min(n + 1, limit) and b == a * a
            wide += 1
    rejected = 0
    for limit in (-1, True, 1.5):
        try:
            model.widths(limit)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(limit)
    return {
        "question_id": "PREP-140",
        "status": "passed",
        "finite_limits": 257,
        "trajectory_samples": steps,
        "reset_cases": reset_cases,
        "wide_boundary_cases": wide,
        "invalid_limits_rejected": rejected,
        "scope": "Python simultaneous-old-state recurrence against integer square; exact specified widths and saturation checked. No HDL compilation, synthesis or timing claim.",
    }


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-140-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))
