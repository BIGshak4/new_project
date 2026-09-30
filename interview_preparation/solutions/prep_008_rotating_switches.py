"""Exact model of four invisible toggle switches and arbitrary quarter-turns.

Bits 0..3 are the visible corners clockwise: TL, TR, BR, BL.
A press mask toggles that subset simultaneously. Uniform states succeed.
"""

from collections import deque

GOALS = frozenset((0, 15))
INITIAL = frozenset(range(1, 15))
ODD = frozenset(s for s in INITIAL if s.bit_count() % 2)
DIAGONAL = frozenset((5, 10))
ADJACENT = INITIAL - ODD - DIAGONAL
STRATEGY = (5, 3, 5, 1, 5, 3, 5)  # diagonal, adjacent, diagonal, single, ...


def rotate(state, quarter_turns):
    return ((state << quarter_turns) | (state >> (4 - quarter_turns))) & 15


def after_failure(possible_states, press_mask):
    result = set()
    for state in possible_states:
        updated = state ^ press_mask
        if updated not in GOALS:
            result.update(rotate(updated, turn) for turn in range(4))
    return frozenset(result)


def shortest_strategy(start=INITIAL):
    queue = deque([(start, ())])
    seen = {start}
    while queue:
        states, path = queue.popleft()
        if not states:
            return path
        for action in range(16):
            following = after_failure(states, action)
            if following not in seen:
                seen.add(following)
                queue.append((following, path + (action,)))
    return None


def belief_name(states):
    if not states:
        return "empty"
    names = []
    for name, group in (("O", ODD), ("A", ADJACENT), ("D", DIAGONAL)):
        if states & group:
            assert group <= states
            names.append(name)
    return "+".join(names)


if __name__ == "__main__":
    print("Shortest press masks:", shortest_strategy())
    states = INITIAL
    print(belief_name(states))
    for action in STRATEGY:
        states = after_failure(states, action)
        print(f"press {action:04b}: {belief_name(states)}")
