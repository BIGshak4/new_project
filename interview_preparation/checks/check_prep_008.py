"""Exhaustive reachability, minimality and path checks for PREP-008."""

import importlib.util
from itertools import product
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "solutions" / "prep_008_rotating_switches.py"
spec = importlib.util.spec_from_file_location("rotating_switches", path)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)

best = model.shortest_strategy()
assert len(best) == 7, best
states = model.INITIAL
expected = ["O+A+D", "O+A", "O+D", "O", "A+D", "A", "D", "empty"]
assert model.belief_name(states) == expected[0]
for action, name in zip(model.STRATEGY, expected[1:]):
    states = model.after_failure(states, action)
    assert model.belief_name(states) == name
assert not states

# Every initial nonuniform state, every rotation choice between seven attempts.
paths = 0
latest_success = 0
for initial in model.INITIAL:
    for rotations in product(range(4), repeat=6):
        state = initial
        for index, action in enumerate(model.STRATEGY):
            state ^= action
            if state in model.GOALS:
                latest_success = max(latest_success, index + 1)
                break
            if index < 6:
                state = model.rotate(state, rotations[index])
        else:
            raise AssertionError((initial, rotations))
        paths += 1
assert latest_success == 7

print(f"PASS: {paths} initial-state/rotation paths; latest success at attempt {latest_success}.")
print("PASS: BFS considers all 16 simultaneous press masks; shortest guaranteed strategy has length 7.")
print("Belief state | minimum remaining attempts | successors S, A, D, no-op")
groups = [model.ODD, model.ADJACENT, model.DIAGONAL]
for included in product((False, True), repeat=3):
    belief = frozenset().union(*(group for use, group in zip(included, groups) if use))
    distance = len(model.shortest_strategy(belief))
    successors = [model.belief_name(model.after_failure(belief, action)) for action in (1, 3, 5, 0)]
    print(model.belief_name(belief), distance, successors)
