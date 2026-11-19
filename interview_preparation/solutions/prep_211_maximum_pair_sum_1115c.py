"""Largest sum at two distinct positions in a single input traversal.

Natural values include zero. Exact Python integers avoid arithmetic overflow.
Return None when fewer than two values exist. The input iterable is not mutated.
"""


def maximum_pair_sum(values):
    largest = second = None
    for value in values:
        if type(value) is not int or value < 0:
            raise ValueError("nonnegative exact integers required")
        if largest is None or value >= largest:
            second, largest = largest, value
        elif second is None or value > second:
            second = value
    return None if second is None else largest + second
