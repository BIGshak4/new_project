"""Clock-edge model of a first-finisher register with lane-1-first tie priority.

Input pulses are already synchronous and stable at each clock edge. This model
does not debounce physical switches or recover subcycle event ordering.
"""


def next_winner(winner: int, p1: int, p2: int, p3: int, reset: bool = False) -> int:
    """Return 0 for no winner, or the latched lane number 1, 2, or 3."""
    if winner not in (0, 1, 2, 3) or any(p not in (0, 1) for p in (p1, p2, p3)):
        raise ValueError("Require winner 0..3 and binary finish pulses")
    if reset:
        return 0
    if winner != 0:
        return winner
    if p1:
        return 1
    if p2:
        return 2
    if p3:
        return 3
    return 0


class FirstFinisher:
    """Output changes only on a modeled rising clock edge."""

    def __init__(self):
        self.winner = 0

    def step(self, p1: int, p2: int, p3: int, reset: bool = False) -> int:
        self.winner = next_winner(self.winner, p1, p2, p3, reset)
        return self.winner
