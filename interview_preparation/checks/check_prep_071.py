"""Independent exact-arithmetic checks for PREP-071."""

import json
from fractions import Fraction
from importlib.util import module_from_spec, spec_from_file_location
from itertools import combinations, permutations, product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = spec_from_file_location(
    "midpoint_solution", BANK / "solutions/prep_071_integer_midpoint.py"
)
solution = module_from_spec(spec)
spec.loader.exec_module(solution)


def midpoint(a, b):
    average = tuple(Fraction(x + y, 2) for x, y in zip(a, b))
    return average if all(value.denominator == 1 for value in average) else None


def validate(points, dimension):
    expected = any(midpoint(a, b) is not None for a, b in combinations(points, 2))
    result = solution.first_midpoint_pair(points, dimension)
    assert (result is not None) == expected
    if result:
        a, b, center = result
        assert a != b and a in points and b in points
        assert tuple(midpoint(a, b)) == center


def run():
    scalar_cases = 0
    for count in range(4):
        for points in permutations([(v,) for v in range(1, 7)], count):
            validate(points, 1)
            scalar_cases += 1
    grid = list(product(range(1, 5), repeat=2))
    two_d_cases = 0
    for count in range(6):
        for points in combinations(grid, count):
            validate(points, 2)
            two_d_cases += 1
    witness_dimensions = 0
    for dimension in range(1, 7):
        points = list(product((1, 2), repeat=dimension))
        assert len(points) == 2**dimension
        assert all(midpoint(a, b) is None for a, b in combinations(points, 2))
        assert solution.first_midpoint_pair(points, dimension) is None
        extra = (3,) * dimension
        result = solution.first_midpoint_pair(points + [extra], dimension)
        assert result is not None and tuple(midpoint(result[0], result[1])) == result[2]
        assert solution.guaranteed_draws(dimension) == len(points) + 1
        witness_dimensions += 1
    invalid = [(0, [(1,)]), (1, [(0,)]), (2, [(1,)]), (1, [(True,)]), (1, [(1,), (1,)])]
    for dimension, points in invalid:
        try:
            solution.first_midpoint_pair(points, dimension)
        except ValueError:
            pass
        else:
            raise AssertionError((dimension, points))
    result = {
        "question_id": "PREP-071",
        "checked_on": "2026-10-21",
        "status": "passed_python_model",
        "scalar_ordered_streams": scalar_cases,
        "two_dimensional_subsets": two_d_cases,
        "tight_bound_witness_dimensions": witness_dimensions,
        "rejected_inputs": len(invalid),
        "method": "Independent Fraction-valued pairwise midpoint oracle; all ordered scalar streams of lengths zero through three from 1..6; all subsets of sizes zero through five of the positive 4x4 lattice; lower-bound parity representatives in dimensions 1..6.",
        "limits": "Finite exact arithmetic checks support the general pigeonhole proof; no random sampling, HDL, physical tests or human professional approval.",
    }
    (BANK / "checks/prep-071-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
