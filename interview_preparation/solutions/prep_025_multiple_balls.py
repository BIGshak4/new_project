"""Coverage and exact minimax counts for arbitrary numbers of crystal balls."""
from math import comb


def coverage(balls: int, drops: int) -> int:
    return sum(comb(drops, j) for j in range(1, min(balls, drops) + 1))


def minimum_drops(floors: int, balls: int) -> int:
    if not isinstance(floors, int) or floors < 0:
        raise ValueError('floors must be a nonnegative integer')
    if not isinstance(balls, int) or balls < 0:
        raise ValueError('balls must be a nonnegative integer')
    if floors == 0:
        return 0
    if balls == 0:
        raise ValueError('Cannot distinguish unknown thresholds with no balls')
    drops = 0
    while coverage(balls, drops) < floors:
        drops += 1
    return drops


def search(floors: int, balls: int, breaks):
    """Return threshold, trace. floors+1 denotes no breaking floor."""
    drops = minimum_drops(floors, balls)
    safe, breaking = 0, floors + 1
    trace = []
    while breaking - safe > 1:
        tested = min(breaking - 1, safe + coverage(balls - 1, drops - 1) + 1)
        broken = bool(breaks(tested))
        trace.append((tested, broken, balls, drops))
        drops -= 1
        if broken:
            breaking = tested
            balls -= 1
        else:
            safe = tested
    return breaking, trace
