"""Exact liquid bookkeeping; this does not model perceived colors."""
from fractions import Fraction


def mixed_transfer(red_volume, blue_volume, spoon):
    """Pure initial liquids, equal spoon each way, homogeneous second cup."""
    a, b, s = map(Fraction, (red_volume, blue_volume, spoon))
    if a <= 0 or b <= 0 or s < 0 or s > a:
        raise ValueError("positive initial volumes and 0 <= spoon <= red volume required")
    red_return = s * s / (b + s)
    blue_return = s * b / (b + s)
    return {"red_in_red_cup": a - s + red_return,
            "blue_in_red_cup": blue_return,
            "red_in_blue_cup": s - red_return,
            "blue_in_blue_cup": b - blue_return,
            "foreign_fraction_red_cup": blue_return / a,
            "foreign_fraction_blue_cup": (s - red_return) / b}


def return_any_composition(red_volume, blue_volume, spoon, red_return):
    """Conservation also holds without homogeneous mixing."""
    a, b, s, r = map(Fraction, (red_volume, blue_volume, spoon, red_return))
    if a <= 0 or b <= 0 or s < 0 or s > a or not max(0, s - b) <= r <= s:
        raise ValueError("the returned spoon must contain available red and blue liquid")
    return {"blue_in_red_cup": s - r, "red_in_blue_cup": s - r}
