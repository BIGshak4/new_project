"""Verify PREP-005 fixed sorting networks; no physical timing simulation."""

import json
from itertools import permutations, product
from pathlib import Path


# One-based channel indices; lower-index output always receives min.
SORT4 = [(1, 2), (3, 4), (1, 3), (2, 4), (2, 3)]
SECOND = [(3, 4), (5, 6), (3, 5), (4, 6), (4, 5)]
FULL6 = SORT4 + SECOND + SORT4
REMOVED = {5, 10, 11}  # zero-based comparator positions in FULL6
OPT6 = [pair for index, pair in enumerate(FULL6) if index not in REMOVED]


def run(values, network):
    result = list(values)
    for i, j in network:
        result[i - 1], result[j - 1] = min(result[i - 1], result[j - 1]), max(result[i - 1], result[j - 1])
    return result


def three_blocks(values):
    result = list(values)
    for start in (0, 2, 0):
        result[start:start + 4] = sorted(result[start:start + 4])
    return result


def check_removed(values):
    state = list(values)
    for index, (i, j) in enumerate(FULL6):
        if index in REMOVED:
            assert state[i - 1] <= state[j - 1], (values, index, state)
        state[i - 1], state[j - 1] = min(state[i - 1], state[j - 1]), max(state[i - 1], state[j - 1])


assert len(SORT4) == 5 and len(FULL6) == 15 and len(OPT6) == 12
bank = json.loads((Path(__file__).resolve().parents[1] / "questions.json").read_text(encoding="utf-8"))
question = next(q for q in bank["questions"] if q["id"] == "PREP-005")
stored = question["solution_networks"]
assert stored["sort4"] == [list(pair) for pair in SORT4]
assert stored["sort6_optimized"] == [list(pair) for pair in OPT6]
assert stored["sort6_blocks"] == [[1, 2, 3, 4], [3, 4, 5, 6], [1, 2, 3, 4]]
assert question["translations"]["he"]["hints"] == [hint["content"] for hint in question["prepared_hints"]]
four_cases = list(product((0, 1), repeat=4)) + list(permutations(range(4)))
for case in four_cases:
    assert run(case, SORT4) == sorted(case)
six_cases = list(product((0, 1), repeat=6)) + list(permutations(range(6))) + list(product((-1, 0, 1), repeat=6))
for case in six_cases:
    expected = sorted(case)
    assert three_blocks(case) == run(case, FULL6) == run(case, OPT6) == expected
    check_removed(case)
print(f"PASS: 4-input sorter: {len(four_cases)} cases (16 binary + 24 permutations).")
print(f"PASS: 6-input sorters: {len(six_cases)} cases (64 binary + 720 permutations + 729 ternary).")
print("PASS: all three removed comparisons were already ordered in every checked case.")
print("Zero-one coverage establishes sorting correctness for totally ordered values; minimum size is a separately cited result.")
