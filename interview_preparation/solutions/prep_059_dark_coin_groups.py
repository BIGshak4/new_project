"""Plan a blind coin split without reading or detecting coin orientations.

The output contains indices only: select the first known_tails coins and flip
exactly those indices. The caller may choose any fixed indexing of the coins.
No orientation data is accepted by the plan, so it cannot exploit hidden data.
"""


def blind_plan(total_coins: int, known_tails: int = 10):
    if (type(total_coins) is not int or type(known_tails) is not int
            or not 0 < known_tails < total_coins):
        raise ValueError("require integers 0 < known_tails < total_coins")
    group_a = tuple(range(known_tails))
    group_b = tuple(range(known_tails, total_coins))
    flip_indices = group_a
    return group_a, group_b, flip_indices
