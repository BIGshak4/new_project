"""Exact finite river-puzzle model; literal and explicitly relaxed contracts.

State is (wolves_on_far_bank, sheep_on_far_bank, boat_bank), bank 0/1.
Boat passengers count toward the destination bank during a crossing.
"""

from collections import deque
from itertools import product


def safe_bank(wolves, sheep, *, allow_no_sheep=True):
    return (allow_no_sheep and sheep == 0) or wolves <= sheep


def state_graph(*, relaxed=False, allow_no_sheep=True):
    states = [state for state in product(range(4), range(4), range(2))
              if safe_bank(state[0], state[1], allow_no_sheep=allow_no_sheep)
              and safe_bank(3 - state[0], 3 - state[1], allow_no_sheep=allow_no_sheep)]
    graph = {state: [] for state in states}
    for wolves, sheep, boat in states:
        for moved_wolves, moved_sheep in product(range(3), repeat=2):
            passengers = moved_wolves + moved_sheep
            allowed = 1 <= passengers <= 2 if relaxed else passengers == (2 if boat == 0 else 1)
            if not allowed:
                continue
            sign = 1 if boat == 0 else -1
            target = (wolves + sign * moved_wolves, sheep + sign * moved_sheep, 1 - boat)
            # Counts must stay in 0..3 and both arrival/departure banks must be safe.
            if target in graph:
                graph[(wolves, sheep, boat)].append((target, (moved_wolves, moved_sheep)))
    return graph


def analyze(*, relaxed=False, allow_no_sheep=True, all_animals=False):
    graph = state_graph(relaxed=relaxed, allow_no_sheep=allow_no_sheep)
    start = (0, 0, 0)
    distance, previous = {start: 0}, {}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for target, passengers in graph[state]:
            if target not in distance:
                distance[target] = distance[state] + 1
                previous[target] = (state, passengers)
                queue.append(target)
    goals = [state for state in distance if state[1] == 3 and (not all_animals or state[0] == 3)]
    route = None
    if goals:
        goal = min(goals, key=distance.get)
        route = []
        while goal != start:
            source, passengers = previous[goal]
            route.append((source, passengers, goal))
            goal = source
        route.reverse()
    return {"graph": graph, "distance": distance, "route": route}
