"""Exact total-time checks and finite-speed impossibility witnesses."""
import importlib.util
import json
from fractions import Fraction
from itertools import product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("speed_model", BANK / "solutions/prep_146_equal_leg_average_speed.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    cases = attainable = 0
    for d, v1, v2 in product((1, 3, 100), range(1, 41), range(1, 41)):
        actual = model.round_trip_average(d, v1, v2)
        # Independently solve average * elapsed time = total distance.
        assert actual * (Fraction(d, v1) + Fraction(d, v2)) == 2 * d
        assert actual == Fraction(2 * v1 * v2, v1 + v2) < 2 * v1
        assert 2 * v1 - actual == Fraction(2 * v1 * v1, v1 + v2) > 0
        cases += 1
    for v1, denominator in product(range(1, 16), range(2, 20)):
        for numerator in range(1, 2 * denominator):
            ratio = Fraction(numerator, denominator)
            v2 = model.return_speed_for_ratio(v1, ratio)
            assert model.round_trip_average(7, v1, v2) == ratio * v1
            attainable += 1
    # Increasing return speed approaches, never reaches, twice the first speed.
    values = [model.round_trip_average(1, 1, v) for v in (1, 10, 100, 1000, 10000)]
    assert values == sorted(values) and values[-1] < 2
    rejected = 0
    for call in (lambda: model.round_trip_average(0, 1, 1), lambda: model.round_trip_average(1, 0, 1),
                 lambda: model.round_trip_average(1, 1, -1), lambda: model.return_speed_for_ratio(1, 2),
                 lambda: model.return_speed_for_ratio(1, 3), lambda: model.return_speed_for_ratio(1, 0)):
        try:
            call()
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("invalid finite positive trip accepted")
    return {"question_id": "PREP-146", "status": "passed", "exact_trip_cases": cases,
            "attainable_target_ratio_cases": attainable, "limit_sequence_examples": len(values),
            "invalid_cases_rejected": rejected,
            "scope": "Exact rational constant-speed equal-distance arithmetic. No physical driving experiment or infinite-speed execution."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-146-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
