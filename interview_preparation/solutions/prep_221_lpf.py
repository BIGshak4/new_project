"""First-order RC/filter-follower teaching model; not SPICE or device signoff."""
import cmath
import math


def response(r, c, frequency):
    if r <= 0 or c <= 0 or frequency < 0:
        raise ValueError('R,C positive; frequency nonnegative')
    return 1 / (1 + 2j * math.pi * frequency * r * c)


def cutoff(r, c):
    if r <= 0 or c <= 0:
        raise ValueError('R,C must be positive')
    return 1 / (2 * math.pi * r * c)


def step(r, c, vin, initial, time):
    if r <= 0 or c <= 0 or time < 0:
        raise ValueError('Invalid RC step parameters')
    return vin + (initial - vin) * math.exp(-time / (r * c))


def follower(vin, open_loop_gain):
    if open_loop_gain <= 0:
        raise ValueError('Positive DC open-loop gain required')
    return vin * open_loop_gain / (1 + open_loop_gain)


def magnitude_phase(r, c, frequency):
    value = response(r, c, frequency)
    return abs(value), cmath.phase(value)
