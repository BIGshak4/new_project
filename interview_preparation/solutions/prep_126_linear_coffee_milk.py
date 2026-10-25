"""Exact affine cooling branches; the screenshot does not specify postmix slope.

Heat capacities absorb mass and specific heat. Milk is kept at the supplied
temperature until addition; mixing is instantaneous and conserves heat.
No numerical prediction about a real cup or Newton-cooling replacement.
"""

from fractions import Fraction


def linear_schedules(coffee=90, milk=10, coffee_capacity=200, milk_capacity=50,
                     before_slope=1, after_slope=1, delay=10):
    tc, tm, cc, cm, a, b, t = map(Fraction, (coffee, milk, coffee_capacity, milk_capacity,
                                          before_slope, after_slope, delay))
    if cc <= 0 or cm < 0 or min(a, b, t) < 0:
        raise ValueError("positive coffee capacity; other capacities/rates/time nonnegative")
    total = cc + cm
    mixture = (cc * tc + cm * tm) / total
    early = mixture - b * t
    late = (cc * (tc - a * t) + cm * tm) / total
    return {"early": early, "late": late, "late_minus_early": late - early}


def constant_power_schedules(coffee=90, milk=10, coffee_capacity=200, milk_capacity=50,
                             power=200, delay=10):
    tc, tm, cc, cm, p, t = map(Fraction, (coffee, milk, coffee_capacity, milk_capacity, power, delay))
    if cc <= 0 or cm < 0 or min(p, t) < 0:
        raise ValueError("positive coffee capacity; other capacity/power/time nonnegative")
    early = (cc * tc + cm * tm) / (cc + cm) - p * t / (cc + cm)
    late = (cc * (tc - p * t / cc) + cm * tm) / (cc + cm)
    return {"early": early, "late": late, "late_minus_early": late - early}
