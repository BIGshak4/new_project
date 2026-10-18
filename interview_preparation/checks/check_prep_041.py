"""Independent deterministic checks for PREP-041; no archive or DB mutation."""

from __future__ import annotations

import importlib.util
import json
import random
from itertools import combinations, permutations
from pathlib import Path

SOLUTION = Path(__file__).resolve().parents[1] / "solutions" / "prep_041_missing_values.py"
SPEC = importlib.util.spec_from_file_location("prep_041_missing_values", SOLUTION)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def oracle(remaining: list[int] | tuple[int, ...], n: int) -> tuple[int, ...]:
    """Set difference is independent of both sum and XOR implementations."""
    return tuple(sorted(set(range(1, n + 1)) - set(remaining)))


def verify() -> dict[str, object]:
    rng = random.Random(20261018)
    counts = {"single_n100": 0, "pair_n100": 0, "small_all_orders": 0, "size_guards": 0}

    for removed_count in (1, 2):
        solver = MODULE.missing_one if removed_count == 1 else MODULE.missing_two
        key = "single_n100" if removed_count == 1 else "pair_n100"
        for removed in combinations(range(1, 101), removed_count):
            remaining = [value for value in range(1, 101) if value not in removed]
            shuffled = remaining.copy()
            rng.shuffle(shuffled)
            for ordered in (remaining, remaining[::-1], shuffled):
                result = solver(ordered, 100)
                actual = (result,) if removed_count == 1 else result
                assert actual == oracle(ordered, 100) == removed
                counts[key] += 1

    for n in range(1, 8):
        for removed_count in (1, 2):
            if n < removed_count:
                continue
            solver = MODULE.missing_one if removed_count == 1 else MODULE.missing_two
            for removed in combinations(range(1, n + 1), removed_count):
                remaining = [value for value in range(1, n + 1) if value not in removed]
                for ordered in permutations(remaining):
                    result = solver(ordered, n)
                    actual = (result,) if removed_count == 1 else result
                    assert actual == oracle(ordered, n) == removed
                    counts["small_all_orders"] += 1

    for solver, remaining, n in (
        (MODULE.missing_one, [], 0),
        (MODULE.missing_one, [], 2),
        (MODULE.missing_two, [], 1),
        (MODULE.missing_two, [], 3),
    ):
        try:
            solver(remaining, n)
        except ValueError:
            counts["size_guards"] += 1
        else:
            raise AssertionError("Expected explicit size guard to reject the input")

    return {
        "question_id": "PREP-041",
        "interpretation": "A permutation of 1..n has one or two distinct values removed and hidden",
        "counts": counts,
        "total_cases": sum(counts.values()),
        "original_n100_missing_sets": {"singles": 100, "pairs": 4950},
        "small_exhaustive_n": "1..7, all missing sets and all remaining permutations",
        "input_orders_n100": ["ascending", "descending", "deterministically shuffled"],
        "oracle": "independent set difference, used only in verification",
        "limitations": [
            "No inference is claimed if the original input omits the removal/observation model",
            "The algorithms assume uniqueness and the range 1..n; size checks are not full validation",
            "No live website interactions or hardware measurements are performed here",
        ],
        "status": "passed",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
