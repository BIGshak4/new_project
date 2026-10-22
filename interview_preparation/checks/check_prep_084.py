"""Exact small fixed-hook oracle plus symbolic/numeric regular-polygon checks."""
import importlib.util
import json
from itertools import combinations
from math import isclose
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("plate", ROOT / "solutions/prep_084_plate_balance.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def main():
    hooks = [(x, y) for x in (-1, 0, 1) for y in (-1, 0, 1) if (x, y) != (0, 0)]
    examined = 0
    for count in range(9):
        expected = set()
        for chosen in combinations(range(8), count):
            # Independent physical cross-product moment with F=(0,0,-7).
            torque_x = sum(-7 * hooks[index][1] for index in chosen)
            torque_y = sum(7 * hooks[index][0] for index in chosen)
            if torque_x == torque_y == 0:
                expected.add(chosen)
            examined += 1
        assert set(model.balanced_subsets(hooks, count)) == expected
    assert examined == 256
    for count in range(1, 5):
        assert not list(model.balanced_subsets([(1, -2), (1, 0), (2, 1), (3, 2)], count))
    regular_cases = 0
    for count in range(2, 21):
        # Exact coefficient identity: (z-1)(1+z+...+z^(k-1)) = z^k-1.
        product = [0] * (count + 1)
        for power in range(count):
            product[power] -= 1
            product[power + 1] += 1
        assert product == [-1] + [0] * (count - 1) + [1]
        for radius in (0.1, 1.0, 7.0):
            points = model.regular_positions(count, radius)
            assert len(set(points)) == count
            assert isclose(sum(x for x, _ in points), 0, abs_tol=1e-12)
            assert isclose(sum(y for _, y in points), 0, abs_tol=1e-12)
            regular_cases += 1
    rejected = 0
    for call in (lambda: model.regular_positions(1), lambda: model.regular_positions(2, 0),
                 lambda: list(model.balanced_subsets(hooks, -1)),
                 lambda: list(model.balanced_subsets(hooks, 9))):
        try:
            call()
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("Invalid input accepted")
    evidence = {
        "status": "passed", "fixed_hook_subsets_checked": examined,
        "one_half_plane_count_cases_rejected": 4,
        "regular_polygon_counts_symbolically_checked": list(range(2, 21)),
        "regular_polygon_numeric_count_radius_cases": regular_cases,
        "invalid_input_rejections": rejected,
        "independent_oracle": "Integer cross-product torque on all subsets of eight specified hooks; telescoping polynomial coefficient identity for regular polygons.",
        "scope": "Ideal equal positive masses and a centered pivot. Fixed-hook answers require coordinates. No physical stability or experimental validation.",
    }
    (ROOT / "checks/prep-084-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()
