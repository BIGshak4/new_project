"""Check the circle derivation against independently calculated Decimal pi."""
import importlib.util
import json
from decimal import Decimal, localcontext
from math import isclose
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rope", ROOT / "solutions/prep_090_earth_rope.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def arctan_inverse(n):
    x = Decimal(1) / n
    power, total, sign, denominator = x, Decimal(0), 1, 1
    while True:
        term = sign * power / denominator
        new = total + term
        if new == total:
            return total
        total, power = new, power * x * x
        sign, denominator = -sign, denominator + 2


def main():
    with localcontext() as ctx:
        ctx.prec = 100
        pi_decimal = 16 * arctan_inverse(5) - 4 * arctan_inverse(239)
        tested = 0
        for extra in [Decimal(0), Decimal("0.001"), Decimal(1), Decimal(10),
                      Decimal(1000), 2 * pi_decimal]:
            expected = extra / (2 * pi_decimal)
            assert isclose(model.uniform_clearance(extra), float(expected), rel_tol=1e-14, abs_tol=1e-14)
            for radius in [Decimal("0.01"), Decimal(1), Decimal(6371000),
                           Decimal(10) ** 20, Decimal(10) ** 50]:
                old_circumference = 2 * pi_decimal * radius
                new_radius = (old_circumference + extra) / (2 * pi_decimal)
                assert abs((new_radius - radius) - expected) < Decimal("1e-45")
                tested += 1
        assert model.uniform_clearance(10) > 1
        assert model.uniform_clearance(6) < 1
        assert model.extra_length_for_clearance(1) < 10
        rejected = 0
        for value in [-1, float("nan"), float("inf")]:
            for fn in [model.uniform_clearance, model.extra_length_for_clearance]:
                try:
                    fn(value)
                except ValueError:
                    rejected += 1
                else:
                    raise AssertionError(value)
        evidence = {
            "question_id": "PREP-090", "status": "passed",
            "independent_oracle": "100-digit Decimal pi via Machin arctangent identity; full circumference/radius calculation",
            "radius_increment_cases": tested, "invalid_inputs_rejected": rejected,
            "clearance_metres_for_10m": model.uniform_clearance(10),
            "scope": "Ideal concentric circles only; no measured Earth radius or physical rope model needed.",
        }
    (ROOT / "checks/prep-090-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()
