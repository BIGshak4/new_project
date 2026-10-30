"""Abstract identification code; no experiment on people or chemicals."""


def pools(bottles: int = 1000, tasters: int = 10):
    if bottles < 1 or tasters < 0 or bottles > 1 << tasters:
        raise ValueError("insufficient binary outcome patterns")
    return [{public for public in range(1, bottles + 1)
             if ((public - 1) >> bit) & 1} for bit in range(tasters)]


def identify(dead, bottles: int = 1000):
    outcomes = tuple(dead)
    if any(value not in (0, 1, False, True) for value in outcomes):
        raise ValueError("outcomes must be binary")
    label = sum(int(value) << bit for bit, value in enumerate(outcomes))
    if not 0 <= label < bottles:
        raise ValueError("unassigned outcome pattern")
    return label + 1


def permitted_adversarial_death(first_exposure: float) -> float:
    """Allowed independent latency in (0,60]; observation deadline is minute 90."""
    if first_exposure < 0:
        raise ValueError("exposure time must be nonnegative")
    return 60 if first_exposure < 60 else first_exposure + 60
