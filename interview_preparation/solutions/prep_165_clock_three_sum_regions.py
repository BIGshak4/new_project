"""Two parallel ideal chords split ordinary clock marks into sums of26."""

from math import cos, pi


def partition_clock():
    groups = {"upper_cap": [], "middle": [], "lower_cap": []}
    # Normal direction is fifteen degrees clockwise from12. Chords are
    # u dot p=+1/2 and-1/2 on a unit disk, so they do not intersect inside.
    for label in range(1, 13):
        projection = cos(label * pi / 6 - pi / 12)
        region = (
            "upper_cap"
            if projection > 0.5
            else "lower_cap"
            if projection < -0.5
            else "middle"
        )
        groups[region].append(label)
    return {key: tuple(value) for key, value in groups.items()}
