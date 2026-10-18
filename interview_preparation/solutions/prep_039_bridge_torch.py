"""Exact bridge-and-torch solver for PREP-039, using the conventional crossing rules.

Each move carries the torch and one or two people, costs the slowest person's
crossing time, and toggles the torch's side. Waiting cannot lower positive cost.
The Dijkstra solver is intentionally general; the interview answer is a short
five-trip schedule, rather than a requirement to implement graph search.
"""

from collections.abc import Sequence
from heapq import heappop, heappush
from itertools import combinations
from typing import NamedTuple


class Crossing(NamedTuple):
    people: tuple[int, ...]
    to_right: bool
    duration: int


def validate_times(times: Sequence[int]) -> tuple[int, ...]:
    values = tuple(times)
    if not values or any(type(value) is not int or value <= 0 for value in values):
        raise ValueError("Crossing times must be a nonempty sequence of positive integers")
    return values


def shortest_crossing(times: Sequence[int]) -> tuple[int, list[Crossing]]:
    """Return exact minimum elapsed time and a witness schedule.

    Bit i of mask is one iff person i is on the right bank. Torch side zero is
    left; side one is right. There are at most 2**(n+1) states and O(n*n)
    possible transitions per state. For varying n, the straightforward search
    has O(2**n * n**3) time and O(2**n * n**2) memory with a lazy binary heap;
    this is an exact verification method, not a claimed efficient general solver.
    """
    values = validate_times(times)
    n = len(values)
    start = (0, 0)
    goal = ((1 << n) - 1, 1)
    distance = {start: 0}
    predecessor = {}
    queue = [(0, *start)]
    while queue:
        cost, mask, torch_side = heappop(queue)
        state = (mask, torch_side)
        if cost != distance[state]:
            continue
        if state == goal:
            steps = []
            while state != start:
                previous, crossing = predecessor[state]
                steps.append(crossing)
                state = previous
            return cost, list(reversed(steps))
        available = [i for i in range(n) if ((mask >> i) & 1) == torch_side]
        for group_size in (1, 2):
            for group in combinations(available, group_size):
                changed = sum(1 << i for i in group)
                following = (mask ^ changed, 1 - torch_side)
                duration = max(values[i] for i in group)
                proposed = cost + duration
                if proposed < distance.get(following, float("inf")):
                    distance[following] = proposed
                    predecessor[following] = (
                        state, Crossing(group, torch_side == 0, duration)
                    )
                    heappush(queue, (proposed, *following))
    raise AssertionError("A positive-time instance with at least one person is reachable")


def puzzle_schedule() -> list[Crossing]:
    """A=0 needs 1 hour, B=1 needs 2, C=2 needs 4, and D=3 needs 5."""
    return [
        Crossing((0, 1), True, 2),
        Crossing((0,), False, 1),
        Crossing((2, 3), True, 5),
        Crossing((1,), False, 2),
        Crossing((0, 1), True, 2),
    ]


def check_schedule(times: Sequence[int], schedule: Sequence[Crossing]) -> int:
    """Independently replay the supplied directions and torch movements."""
    values = validate_times(times)
    side = [False] * len(values)
    torch_on_right = False
    elapsed = 0
    for crossing in schedule:
        group = crossing.people
        if not 1 <= len(group) <= 2 or len(group) != len(set(group)):
            raise ValueError("A crossing requires one or two distinct people")
        if any(type(i) is not int or not 0 <= i < len(values) for i in group):
            raise ValueError("Invalid person index")
        if crossing.to_right == torch_on_right:
            raise ValueError("Torch is on the wrong bank for the given direction")
        if any(side[i] != torch_on_right for i in group):
            raise ValueError("A selected person is not beside the torch")
        if crossing.duration != max(values[i] for i in group):
            raise ValueError("Pair duration must equal the slower crossing time")
        elapsed += crossing.duration
        torch_on_right = not torch_on_right
        for i in group:
            side[i] = torch_on_right
    if not all(side):
        raise ValueError("Not everyone reached the destination")
    return elapsed


if __name__ == "__main__":
    times = (1, 2, 4, 5)
    optimum, _ = shortest_crossing(times)
    schedule = puzzle_schedule()
    assert check_schedule(times, schedule) == optimum == 12
    elapsed = 0
    for crossing in schedule:
        elapsed += crossing.duration
        names = ", ".join("ABCD"[i] for i in crossing.people)
        print(f"{names} {'->' if crossing.to_right else '<-'} "
              f"{crossing.duration} h; total {elapsed} h")
    print(f"Minimum: {optimum} hours; 12-hour battery is exactly sufficient.")
