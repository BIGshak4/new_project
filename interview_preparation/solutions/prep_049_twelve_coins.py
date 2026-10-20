"""Identify the single odd coin and its direction using exactly three weighings.

The callback receives coin labels on the LEFT and RIGHT pans and returns
"left" (left heavier), "balance", or "right" (right heavier).
No initially known genuine coin is assumed. Coins are labelled 1..12.
"""
from collections.abc import Callable, Sequence

OUTCOMES = ("left", "balance", "right")
FIRST = ((1, 2, 3, 4), (5, 6, 7, 8))
SECOND = {
    "balance": ((9, 10, 11), (1, 2, 3)),
    "left": ((1, 2, 5), (3, 6, 9)),
    "right": ((1, 2, 5), (3, 6, 9)),
}
# Each entry: third weighing, then diagnoses for LEFT / BALANCE / RIGHT.
# None means the observed sequence contradicts the puzzle's assumptions.
FINAL = {
    ("balance", "left"): (((9,), (10,)), ((9, "heavy"), (11, "heavy"), (10, "heavy"))),
    ("balance", "balance"): (((12,), (1,)), ((12, "heavy"), None, (12, "light"))),
    ("balance", "right"): (((9,), (10,)), ((10, "light"), (11, "light"), (9, "light"))),
    ("left", "left"): (((1,), (2,)), ((1, "heavy"), (6, "light"), (2, "heavy"))),
    ("left", "balance"): (((7,), (8,)), ((8, "light"), (4, "heavy"), (7, "light"))),
    ("left", "right"): (((3,), (9,)), ((3, "heavy"), (5, "light"), None)),
    ("right", "left"): (((3,), (9,)), (None, (5, "heavy"), (3, "light"))),
    ("right", "balance"): (((7,), (8,)), ((7, "heavy"), (4, "light"), (8, "heavy"))),
    ("right", "right"): (((1,), (2,)), ((2, "light"), (6, "heavy"), (1, "light"))),
}


def next_weighing(history: Sequence[str]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Return the next pair of pans, using only previous balance outcomes."""
    if any(o not in OUTCOMES for o in history):
        raise ValueError("Unknown balance outcome")
    if len(history) == 0:
        return FIRST
    if len(history) == 1:
        return SECOND[history[0]]
    if len(history) == 2:
        return FINAL[tuple(history)][0]
    raise ValueError("Exactly three weighings are available")


def diagnose(history: Sequence[str]) -> tuple[int, str]:
    """Decode three outcomes; reject inconsistent observations."""
    if len(history) != 3 or any(o not in OUTCOMES for o in history):
        raise ValueError("Need exactly three valid outcomes")
    answer = FINAL[tuple(history[:2])][1][OUTCOMES.index(history[2])]
    if answer is None:
        raise ValueError("Outcomes contradict exactly one odd coin and a perfect balance")
    return answer


def identify(weigh: Callable[[tuple[int, ...], tuple[int, ...]], str]) -> tuple[int, str]:
    """Use the physical balance three times; never read hidden coin weights."""
    history = []
    for _ in range(3):
        left, right = next_weighing(history)
        outcome = weigh(left, right)
        if outcome not in OUTCOMES:
            raise ValueError("Unknown balance outcome")
        history.append(outcome)
    return diagnose(history)
