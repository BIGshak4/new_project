"""Safe strict Nyquist-zone intervals for a real contiguous analog band.

Rates/edges use exact rational arithmetic. Positive band edges stay strictly
inside one Nyquist zone, avoiding ambiguous boundary tones; baseband DC is
allowed. The rate has positive geometric margin, but no physical ADC/filter
is designed here.
"""
from fractions import Fraction


def safe_intervals(low, high):
    low, high = Fraction(low), Fraction(high)
    if not 0 <= low < high:
        raise ValueError('Require 0 <= low < high')
    bandwidth = high - low
    ratio = high / bandwidth
    # Largest integer m strictly below high/bandwidth, except baseband m=1.
    max_m = max(1, (ratio.numerator - 1) // ratio.denominator)
    result = []
    for m in range(1, max_m + 1):
        lower = 2 * high / m
        upper = None if m == 1 else 2 * low / (m - 1)
        if upper is None or lower < upper:
            result.append((m, lower, upper))
    return result


def is_safe_rate(low, high, rate):
    rate = Fraction(rate)
    return rate > 0 and any(lower < rate and (upper is None or rate < upper)
                            for _, lower, upper in safe_intervals(low, high))


def fold_frequency(frequency, rate):
    rate = Fraction(rate)
    if rate <= 0:
        raise ValueError('Sampling rate must be positive')
    residue = Fraction(frequency) % rate
    return min(residue, rate - residue)
