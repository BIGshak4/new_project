"""Independent exhaustive two-sum checks; no database or registration writes."""

import importlib.util
import itertools
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prep040", ROOT / "solutions/prep_040_two_sum.py"
)
MODEL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODEL)


def oracle(values, target):
    """Enumerate independent index combinations rather than hash complements."""
    return any(values[i] + values[j] == target
               for i, j in itertools.combinations(range(len(values)), 2))


def check_case(values, target, expected=None):
    before = list(values)
    answer = oracle(values, target)
    if expected is not None:
        assert answer is expected, (values, target, answer, expected)
    for solver in (MODEL.has_pair_quadratic, MODEL.has_pair_sum,
                   MODEL.has_pair_sum_sorted):
        result = solver(values, target)
        assert result is answer, (solver.__name__, values, target, result, answer)
        assert list(values) == before, "Input was mutated"
    indices = MODEL.pair_sum_indices(values, target)
    assert (indices is not None) is answer, (values, target, indices, answer)
    if indices is not None:
        i, j = indices
        assert 0 <= i < j < len(values)
        assert values[i] + values[j] == target
    assert list(values) == before


def verify():
    arrays = 0
    exhaustive_cases = 0
    for size in range(7):
        for array in itertools.product((-2, -1, 0, 1, 2), repeat=size):
            arrays += 1
            for target in range(-5, 6):
                check_case(list(array), target)
                exhaustive_cases += 1

    explicit = [
        ([], 0, False),
        ([6], 12, False),
        ([6, 6], 12, True),
        ([0], 0, False),
        ([0, 0], 0, True),
        ([1, 2, 3], 7, False),
        ([4, 1, 7, 3], 8, True),
        ([-8, -2, 4, 10], -10, True),
        ([-8, -2, 4, 10], 2, True),
        ([5, 5, 5, 5], 10, True),
        ([5, 5, 5, 5], 11, False),
        ([2**63 - 1, 1], 2**63, True),
        ([-2**63, -1], -2**63 - 1, True),
        ([10**300, -(10**300), 3], 0, True),
        ([10**300, 1], 2 * 10**300, False),
        ([10**300, 10**300], 2 * 10**300, True),
    ]
    for values, target, expected in explicit:
        check_case(values, target, expected)

    # Distinct integer keys with identical Python hashes remain functionally
    # correct; this does NOT establish a linear worst-case runtime guarantee.
    modulus = sys.hash_info.modulus
    colliding = [modulus * i for i in range(40)]
    assert len({hash(value) for value in colliding}) == 1
    check_case(colliding, modulus * 77, True)
    check_case(colliding, 1, False)

    rng = random.Random(40)
    randomized = 1000
    for _ in range(randomized):
        values = [rng.randint(-1000, 1000) for _ in range(rng.randrange(101))]
        target = rng.randint(-2500, 2500)
        check_case(values, target)

    # The documented Sequence input also accepts immutable tuples.
    tuple_cases = [((), 0), ((6,), 12), ((6, 6), 12), ((-7, 0, 7), 0)]
    for values, target in tuple_cases:
        check_case(values, target)

    return {
        "question": "PREP-040",
        "status": "passed",
        "checked_on": "2026-10-18",
        "exhaustive_array_alphabet": [-2, -1, 0, 1, 2],
        "exhaustive_array_lengths": [0, 6],
        "exhaustive_arrays": arrays,
        "targets_per_array": 11,
        "exhaustive_array_target_cases": exhaustive_cases,
        "explicit_boundary_cases": len(explicit),
        "python_hash_collision_cases": 2,
        "seeded_random_cases": randomized,
        "immutable_sequence_cases": len(tuple_cases),
        "total_cases": exhaustive_cases + len(explicit) + 2 + randomized + len(tuple_cases),
        "implementations_checked_per_case": 4,
        "oracle": "Independent enumeration of all distinct index combinations",
        "properties": [
            "Boolean solvers match oracle",
            "Optional returned indices are in range, different, and sum to target",
            "Original input remains unchanged after every solver",
            "Single occurrence cannot be reused; duplicate values at different indices can",
            "Python arbitrary-precision integer boundaries remain correct"
        ],
        "scope": "Finite exhaustive tests, boundary/hash-collision cases and seeded sampling; "
                 "complexity is justified separately under an explicit operation model. "
                 "No human technical review or benchmark claim."
    }


if __name__ == "__main__":
    report = verify()
    path = ROOT / "checks/prep-040-verification.json"
    path.write_bytes((json.dumps(report, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8"))
    print(json.dumps(report))
