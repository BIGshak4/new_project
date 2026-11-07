"""Selected teaching contract; these rules are additions, not source facts."""
from fractions import Fraction
from itertools import pairwise


def positions(day, last_label=100):
    if type(day) is not int or day < 0:
        raise ValueError("day must be a nonnegative integer")
    if type(last_label) is not int or last_label < 1:
        raise ValueError("last label must be a positive integer")
    return 1 + 2 * day, last_label - day * (day + 3) // 2


def analyze(last_label=100):
    """Paint only at integer days; travel linearly between valid paint events."""
    # Validate even if a future caller changes how the loop is entered.
    positions(0, last_label)
    visits = []
    day = 0
    while True:
        left, right = positions(day, last_label)
        if not (1 <= left <= last_label and 1 <= right <= last_label):
            break
        visits.append((day, left, right))
        day += 1
    same_day = [(day, left) for day, left, right in visits if left == right]
    crossing = (Fraction(0), Fraction(visits[0][1])) if visits[0][1] == visits[0][2] else None
    for (day, left, right), (_, next_left, next_right) in pairwise(visits):
        gap, next_gap = right - left, next_right - next_left
        if crossing is None and gap >= 0 >= next_gap:
            fraction = Fraction(gap, gap - next_gap)
            crossing = (Fraction(day) + fraction, Fraction(left) + fraction * (next_left - left))
            break
    return {"visits": visits, "same_day": same_day, "continuous_crossing": crossing}
