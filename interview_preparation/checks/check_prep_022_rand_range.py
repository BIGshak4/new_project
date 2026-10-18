"""Exhaust random-choice paths and verify in-place mutation and exact bounds."""
import importlib.util
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rand_range_shuffle", ROOT / "solutions/prep_022_rand_range_shuffle.py")
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)


def verify():
    paths = 0
    for n in range(8):
        bounds = list(range(n - 1, 0, -1))
        outputs = set()
        for choices in itertools.product(*(range(i + 1) for i in bounds)):
            draws = iter(choices)
            calls = []

            def rand_range(low, high, _calls=calls, _draws=draws):
                _calls.append((low, high))
                return next(_draws)

            values = list(range(1, n + 1))
            identity = id(values)
            result = MODEL.shuffle_in_place(values, rand_range)
            assert result is None and id(values) == identity
            assert sorted(values) == list(range(1, n + 1))
            assert calls == [(0, i) for i in bounds]
            outputs.add(tuple(values))
            paths += 1
        assert len(outputs) == math.factorial(n), (n, len(outputs))

    boundary_runs = 0
    for n in (0, 1, 2, 100, 1000):
        for endpoint in ("low", "high"):
            values = list(range(1, n + 1))
            calls = []

            def endpoint_rng(low, high, _calls=calls, _endpoint=endpoint):
                _calls.append((low, high))
                return low if _endpoint == "low" else high

            MODEL.shuffle_in_place(values, endpoint_rng)
            assert sorted(values) == list(range(1, n + 1))
            assert len(calls) == max(n - 1, 0)
            if endpoint == "high":
                assert values == list(range(1, n + 1)), "The original order is a valid permutation"
            boundary_runs += 1
    for initial in ([9, -2, 42, 0], [5, 5, 8], [3, 1, 2]):
        values = list(initial)
        MODEL.shuffle_in_place(values, lambda low, high: low)
        assert sorted(values) == sorted(initial)
    for invalid in (-1, 3, 0.5, True):
        try:
            MODEL.shuffle_in_place([1, 2, 3], lambda low, high, _invalid=invalid: _invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid bounded draw accepted")
    return {"question": "PREP-022", "variant": "hundred-array-rand-range", "status": "passed",
            "exhaustive_paths_n_0_to_7": paths, "distinct_outputs_each_n": "exactly n!",
            "in_place_and_rng_bounds_checked_on_every_path": True,
            "deterministic_boundary_runs": boundary_runs, "nonstandard_input_arrays_checked": 3,
            "invalid_rng_values_rejected": 4, "calls_for_n_100": 99,
            "scope": "Exact path-to-permutation enumeration, not a statistical or cryptographic RNG quality test."}


if __name__ == "__main__":
    report = verify()
    (ROOT / "checks/prep-022-rand-range-verification.json").write_bytes(
        (json.dumps(report, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8"))
    print(json.dumps(report))
