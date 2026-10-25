"""Actual in-place code checked against a frequency-based independent oracle."""
import importlib.util
import itertools
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("numeric_partition", ROOT / "solutions/prep_019_numeric_partition.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


class CountedList(list):
    """Test instrumentation only; never used by the proposed implementation."""
    def __init__(self, values):
        super().__init__(values)
        self.reads = self.writes = 0

    def __getitem__(self, index):
        assert isinstance(index, int), "no array slicing in the actual implementation"
        self.reads += 1
        return super().__getitem__(index)

    def __setitem__(self, index, value):
        assert isinstance(index, int)
        self.writes += 1
        return super().__setitem__(index, value)


def check_case(source):
    values = CountedList(source)
    counts = [sum(value == digit for value in source) for digit in (0, 1, 2)]
    expected = [0] * counts[0] + [1] * counts[1] + [2] * counts[2]
    identity = id(values)
    assert model.partition_012(values) is None
    assert id(values) == identity and values == expected
    assert values.reads <= 3 * len(source) and values.writes <= 2 * len(source)


def verify():
    exhaustive = 0
    for length in range(9):
        for values in itertools.product((0, 1, 2), repeat=length):
            check_case(values)
            exhaustive += 1
    rng = random.Random(20261025)
    for _ in range(300):
        check_case([rng.randrange(3) for _ in range(rng.randrange(501))])
    invalid = 0
    for value in (-1, 3, True, 1.0, "0"):
        try:
            model.partition_012([value])
        except ValueError:
            invalid += 1
        else:
            raise AssertionError("invalid value was accepted")
    return {"status": "passed", "exhaustive_ternary_words": exhaustive,
            "random_arrays": 300, "invalid_values_rejected": invalid,
            "read_bound_per_case": "at most3n element reads", "write_bound_per_case": "at most2n element writes",
            "scope": "Executed Python in-place model with external test instrumentation; no second validation traversal."}


if __name__ == "__main__":
    result = verify()
    (ROOT / "checks/prep-019-numeric-variant-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
