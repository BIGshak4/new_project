"""Select the fastest three using only a five-horse ranking oracle."""


def fastest_three(horses, race):
    """race(ids) returns those five IDs in fastest-first order; no times."""
    if len(horses) != 25 or len(set(horses)) != 25:
        raise ValueError("Expected 25 distinct horse IDs")
    groups = [list(race(horses[i:i + 5])) for i in range(0, 25, 5)]
    by_winner = {group[0]: group for group in groups}
    winners = race([group[0] for group in groups])
    a, b, c, _, _ = [by_winner[winner] for winner in winners]
    finalists = race([a[1], a[2], b[0], b[1], c[0]])
    return [a[0], finalists[0], finalists[1]]
