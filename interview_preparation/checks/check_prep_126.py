"""Independent energy balances and exact affine-slope comparison cases."""

import importlib.util
import json
from fractions import Fraction
from itertools import product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("coffee_model", BANK / "solutions/prep_126_linear_coffee_milk.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    comparisons = power_cases = arbitrary_slopes = 0
    for cc, cm, tc, tm, a, t in product((1, 2, 5), (0, 1, 3), (50, 90), (0, 10, 20),
                                       (Fraction(0), Fraction(1, 2), Fraction(1)), (0, 1, 10)):
        alpha = Fraction(cc, cc + cm)
        actual = model.linear_schedules(tc, tm, cc, cm, a, a, t)
        # An independent total-energy account distinguishes the two exposures.
        initial_energy = cc * tc + cm * tm
        expected_early = (initial_energy - (cc + cm) * a * t) / (cc + cm)
        expected_late = (initial_energy - cc * a * t) / (cc + cm)
        assert actual["early"] == expected_early and actual["late"] == expected_late
        assert actual["late_minus_early"] == (1 - alpha) * a * t >= 0
        comparisons += 1
        p = cc * a  # Same initial coffee slope as the other model.
        power = model.constant_power_schedules(tc, tm, cc, cm, p, t)
        expected = (Fraction(initial_energy) - p * t) / (cc + cm)
        assert power["early"] == power["late"] == expected
        power_cases += 1
        for b in (alpha * a / 2, alpha * a, a):
            result = model.linear_schedules(tc, tm, cc, cm, a, b, t)
            assert result["late_minus_early"] == (b - alpha * a) * t
            arbitrary_slopes += 1
    assert model.linear_schedules() == {"early": 64, "late": 66, "late_minus_early": 2}
    assert model.constant_power_schedules() == {"early": 66, "late": 66, "late_minus_early": 0}
    # Three strictly positive postmix slopes can yield any comparison sign.
    signs = [model.linear_schedules(after_slope=b)["late_minus_early"] for b in (Fraction(2, 5), Fraction(4, 5), 1)]
    assert signs[0] < 0 and signs[1] == 0 and signs[2] > 0
    rejected = 0
    for call in (lambda: model.linear_schedules(coffee_capacity=0),
                 lambda: model.linear_schedules(milk_capacity=-1),
                 lambda: model.linear_schedules(before_slope=-1),
                 lambda: model.linear_schedules(after_slope=-1),
                 lambda: model.linear_schedules(delay=-1),
                 lambda: model.constant_power_schedules(power=-1)):
        try:
            call()
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("invalid affine model accepted")
    return {"question_id": "PREP-126", "status": "passed", "equal_temperature_slope_cases": comparisons,
            "constant_power_energy_cases": power_cases, "general_postmix_slope_cases": arbitrary_slopes,
            "distinct_valid_comparison_signs": 3, "invalid_cases_rejected": rejected,
            "scope": "Exact rational affine models and independent total-energy accounts, not a physical cooling experiment. Newton cooling is a separately labeled unimplemented extension."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-126-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
