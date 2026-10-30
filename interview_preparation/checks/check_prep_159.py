"""Synthetic specification/measurement boundary tests; no physical paper tested."""
import importlib.util
import json
from fractions import Fraction
from itertools import product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("paper159", BANK / "solutions/prep_159_paper_acceptance_model.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    intervals = 0
    # One millimetre here is an explicitly arbitrary synthetic fixture, NOT an ISO tolerance.
    for offset, radius in product(range(-8, 9), range(5)):
        observed_offsets = set(range(offset - radius, offset + radius + 1))
        allowed_offsets = set(range(-4, 5))
        expected = "pass" if observed_offsets <= allowed_offsets else "fail" if not observed_offsets & allowed_offsets else "inconclusive"
        result = model.interval_decision(210 + Fraction(offset, 4), Fraction(radius, 4), 210, 1)
        assert result == expected
        intervals += 1
    orientations = 0
    for short, long, uncertainty in product((209, 210, 211, 212), (296, 297, 298, 299), (0, Fraction(1, 4))):
        assert model.sheet_dimensions(short, long, uncertainty, 1) == model.sheet_dimensions(long, short, uncertainty, 1)
        orientations += 1
    assert model.sheet_dimensions(210, 297, 0) == {"short_side": "needs_requirement", "long_side": "needs_requirement"}
    counts = 0
    for observed, declared in product(range(103), (None, 0, 1, 50, 100)):
        expected = "needs_requirement" if declared is None else "pass" if observed == declared else "fail"
        assert model.count_decision(observed, declared) == expected
        counts += 1
    rejected = 0
    for call in (lambda: model.interval_decision(1, -1, 1, 0), lambda: model.interval_decision(1, 0, 1, -1),
                 lambda: model.sheet_dimensions(0, 297, 0, 1), lambda: model.count_decision(-1, 1),
                 lambda: model.count_decision(1, True)):
        try:
            call()
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("invalid fixture accepted")
    return {"question_id": "PREP-159", "status": "passed", "synthetic_interval_cases": intervals,
            "orientation_invariance_cases": orientations, "declared_count_cases": counts,
            "invalid_measurement_contracts_rejected": rejected,
            "scope": "Only synthetic acceptance logic and missing-requirement decisions tested. No paper package, sheet count, printer, environment, ISO compliance or product quality was physically tested. The test tolerance is invented solely for boundary fixtures."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-159-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
