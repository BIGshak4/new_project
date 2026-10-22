"""Exhaust all five-stone weak compositions with independent cyclotomic arithmetic."""
import importlib.util
import json
from itertools import combinations_with_replacement
from math import comb, cos, isclose, pi, sin, sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("clock", ROOT / "solutions/prep_085_clock_stones.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def root_sum_remainder(hours):
    """Independent unit roots: sum z^h modulo Phi_12(z)=z^4-z^2+1.

    Multiplying every vector by the same quarter-turn does not change a zero
    sum. This uses no table from the model and no irrational float comparison.
    """
    coefficients = [0] * 13
    for hour in hours:
        coefficients[hour] += 1
    for degree in range(12, 3, -1):
        coefficient = coefficients[degree]
        coefficients[degree] = 0
        coefficients[degree - 2] += coefficient
        coefficients[degree - 4] -= coefficient
    return tuple(coefficients[:4])


def main():
    examined = 0
    expected = set()
    for hours in combinations_with_replacement(range(1, 13), 5):
        independent = root_sum_remainder(hours) == (0, 0, 0, 0)
        assert (model.moment_signature(hours) == (0, 0, 0, 0)) == independent
        if independent:
            expected.add(hours)
        examined += 1
    assert examined == comb(16, 5) == 4368
    assert set(model.balanced_placements()) == expected
    assert tuple(sorted(model.example())) in expected
    # Verify the table's clock orientation separately against trigonometric geometry.
    for hour, (xa, xb, ya, yb) in model.HOUR_VECTORS.items():
        assert isclose((xa + xb * sqrt(3)) / 2, sin(hour * pi / 6), abs_tol=1e-14)
        assert isclose((ya + yb * sqrt(3)) / 2, cos(hour * pi / 6), abs_tol=1e-14)
    assert not list(model.balanced_placements(1))
    assert len(list(model.balanced_placements(2))) == 6
    rotations = 0
    for shift in range(12):
        rotated = tuple(((hour + shift - 1) % 12) + 1 for hour in model.example())
        assert model.moment_signature(rotated) == (0, 0, 0, 0)
        rotations += 1
    rejected = 0
    for call in (lambda: model.moment_signature([0]), lambda: model.moment_signature([13]),
                 lambda: list(model.balanced_placements(-1))):
        try:
            call()
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("Invalid input accepted")
    evidence = {
        "status": "passed", "unordered_five_stone_placements_checked": examined,
        "balanced_placements_found": len(expected),
        "exact_example_hours": model.example(), "example_exact_signature": model.moment_signature(model.example()),
        "rotated_examples_checked": rotations, "hour_table_geometry_checks": 12,
        "two_stone_balanced_pairs": 6, "one_stone_balanced_placements": 0,
        "invalid_input_rejections": rejected,
        "independent_oracle": "Integer polynomial reduction modulo Phi_12(z)=z^4-z^2+1, separate from the model's Q(sqrt(3)) coordinate table.",
        "scope": "All 4368 multisets of five ideal equal stones at twelve fixed marks, stacking allowed. Exact zero static moment; no physical experiment or perturbation stability claim.",
    }
    (ROOT / "checks/prep-085-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()
