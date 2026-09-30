"""Compare the lazy reference array against an ordinary eager array."""

import importlib.util
from itertools import product
from pathlib import Path
import random
import sys

variant = "prep_006_set_all_array_versions.py" if "--numeric" in sys.argv else "prep_006_set_all_array.py"
solution_path = Path(__file__).resolve().parents[1] / "solutions" / variant
spec = importlib.util.spec_from_file_location("prep_006_solution", solution_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SetAllArray = module.SetAllArray


def step(subject, reference, operation):
    kind, index, value = operation
    if kind == "set":
        subject.Set(index, value)
        reference[index] = value
    elif kind == "all":
        subject.SetAll(value)
        reference[:] = [value] * len(reference)
    else:
        assert subject.Get(index) is reference[index]
    for i, expected in enumerate(reference):
        assert subject.Get(i) is expected


operations = [("get", i, None) for i in range(2)]
operations += [("set", i, v) for i in range(2) for v in (0, 1)]
operations += [("all", None, v) for v in (0, 1)]
for sequence in product(operations, repeat=4):
    reference = [None, -1]
    subject = SetAllArray(reference)
    for operation in sequence:
        step(subject, reference, operation)

rng = random.Random(6006)
values = [None, False, 0, -7, "hello", object(), [], {"x": 1}]
reference = list(values)
subject = SetAllArray(reference)
for _ in range(10000):
    step(subject, reference, (rng.choice(("set", "get", "all")), rng.randrange(8), rng.choice(values)))

for initial in ([], [None]):
    subject = SetAllArray(initial)
    subject.SetAll(None)
    subject.SetAll(4)
    for bad_index in (-1, len(initial)):
        for action in (lambda i: subject.Get(i), lambda i: subject.Set(i, 1)):
            try:
                action(bad_index)
            except IndexError:
                pass
            else:
                raise AssertionError("Invalid index was accepted")

shared = []
subject = SetAllArray([None, None])
subject.SetAll(shared)
shared.append("same object")
assert subject.Get(0) is shared and subject.Get(1) is shared
subject.Set(0, None)
assert subject.Get(0) is None and subject.Get(1) is shared

print("PASS: 4096 length-4 operation sequences, 10000 seeded random operations, bounds/empty arrays, None and shared-object identity.")
print("Complexity follows from the fixed work in each method, not a timing benchmark.")
