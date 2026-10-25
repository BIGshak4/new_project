"""Exact first-contact model: climb, rest/slide, repeat; stop at the flower."""

from fractions import Fraction


def first_contact(height=10, climb_rate=2, slide_rate=1, climb_duration=1, rest_duration=1):
    height, up, down, active, rest = map(Fraction, (height, climb_rate, slide_rate, climb_duration, rest_duration))
    if height < 0 or up <= 0 or active <= 0 or down < 0 or rest < 0:
        raise ValueError("invalid height, rates or phase durations")
    if height == 0:
        return Fraction(0), []
    gain, loss = up * active, down * rest
    if height > gain and gain <= loss:
        return None, []  # Every cycle returns to no higher a starting point.
    time = position = Fraction(0)
    trace = []
    while position + gain < height:
        trace.append(("climb", time, time + active, position, position + gain))
        position += gain
        time += active
        after = max(Fraction(0), position - loss)
        trace.append(("rest_slide", time, time + rest, position, after))
        position = after
        time += rest
    finish = time + (height - position) / up
    trace.append(("final_climb", time, finish, position, height))
    return finish, trace
