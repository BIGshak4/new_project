"""Exact tank-only, one-way convoy construction; not a physical fuel simulation."""
from fractions import Fraction


def plan(count=100, capacity=50, litres_per_metre=1):
    if type(count) is not int or count < 0:
        raise ValueError('count must be a nonnegative integer')
    capacity, rate = Fraction(capacity), Fraction(litres_per_metre)
    if capacity <= 0 or rate <= 0:
        raise ValueError('Positive capacity and consumption required')
    position = Fraction(0)
    stages = []
    for active in range(count, 0, -1):
        distance = capacity / (active * rate)
        fuel_each = capacity - rate * distance
        position += distance
        stages.append({'active': active, 'distance': distance, 'position': position,
                       'fuel_before': active * capacity,
                       'fuel_after_driving': active * fuel_each,
                       'donor_fuel': fuel_each if active > 1 else Fraction(0),
                       'fuel_after_transfer': (active - 1) * capacity})
    return position, stages


def max_distance(count=100, capacity=50, litres_per_metre=1):
    """O(n) rational terms, O(1) auxiliary values excluding big-integer storage."""
    if type(count) is not int or count < 0:
        raise ValueError('count must be a nonnegative integer')
    capacity, rate = Fraction(capacity), Fraction(litres_per_metre)
    if capacity <= 0 or rate <= 0:
        raise ValueError('Positive capacity and consumption required')
    distance = Fraction(0)
    for active in range(1, count + 1):
        distance += capacity / (rate * active)
    return distance
