"""Ten uniformly spaced samples; symmetric signed Q15 amplitude 32767."""
import math


def full_table():
    return [round(32767*math.sin(2*math.pi*n/10)) for n in range(10)]


def half_sample(phase):
    if not 0 <= phase < 10:
        raise ValueError("phase must be 0..9")
    half = [0,19260,31163,31163,19260]
    return (-1 if phase >= 5 else 1)*half[phase % 5]


def quarter_sample(phase):
    if not 0 <= phase < 10:
        raise ValueError("phase must be 0..9")
    q = phase % 5
    address = min(q,5-q)
    magnitude = [0,19260,31163][address]
    return -magnitude if phase >= 5 else magnitude
