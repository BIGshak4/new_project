"""Blind operation plan: does not accept or inspect coin orientations."""


def blind_plan(total=30, black_count=3):
    if type(total) is not int or type(black_count) is not int or not 0 < black_count < total:
        raise ValueError("this two-nonempty-group construction needs 0 < black_count < total")
    selected = tuple(range(black_count))
    rest = tuple(range(black_count, total))
    return selected, rest, selected
