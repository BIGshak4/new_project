"""Ten positions in a line; each miss is followed by a compulsory adjacent move."""
from collections import deque

POSITIONS = 10
FULL = (1 << POSITIONS) - 1
PLAN = list(range(2, 10)) + list(range(9, 1, -1))


def after_miss(belief: int, shot: int) -> int:
    """Belief immediately before a shot -> belief before the next shot."""
    if not 1 <= shot <= POSITIONS:
        raise ValueError('shot must be in 1..10')
    survivors = belief & ~(1 << (shot - 1))
    return ((survivors << 1) | (survivors >> 1)) & FULL


def trace(plan=PLAN, initial=FULL):
    states = [initial]
    for shot in plan:
        states.append(after_miss(states[-1], shot))
    return states


def shortest_plan():
    """Exact BFS on possible-position sets; no observation except hit/miss."""
    queue = deque([FULL])
    parent = {FULL: None}
    action = {}
    while queue:
        state = queue.popleft()
        if state == 0:
            plan = []
            while parent[state] is not None:
                plan.append(action[state])
                state = parent[state]
            return list(reversed(plan)), len(parent)
        for shot in range(1, POSITIONS + 1):
            successor = after_miss(state, shot)
            if successor not in parent:
                parent[successor] = state
                action[successor] = shot
                queue.append(successor)
    raise AssertionError('No guaranteed strategy found')
