"""Frequency-folding and ideal filtering illustration, not an ADC simulation."""
from fractions import Fraction
from math import cos, pi


def folded_frequency(frequency, sample_rate):
    f, fs = Fraction(frequency), Fraction(sample_rate)
    if f < 0 or fs <= 0:
        raise ValueError("nonnegative frequency and positive sample rate required")
    remainder = f % fs
    return min(remainder, fs - remainder)


def cosine_samples(frequency, sample_rate, count=32):
    if frequency < 0 or sample_rate <= 0 or count < 0:
        raise ValueError("invalid tone, rate or sample count")
    return [cos(2 * pi * frequency * n / sample_rate) for n in range(count)]


def ideal_lowpass(components, cutoff):
    """Components are (nonnegative frequency, amplitude); brick wall is ideal."""
    if cutoff < 0 or any(f < 0 for f, _ in components):
        raise ValueError("nonnegative frequencies and cutoff required")
    return [(f, amplitude) for f, amplitude in components if f <= cutoff]


def strict_baseband_rate_ok(useful_bandwidth, sample_rate):
    if useful_bandwidth < 0 or sample_rate <= 0:
        raise ValueError("invalid useful bandwidth or sample rate")
    return sample_rate > 2 * useful_bandwidth
