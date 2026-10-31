"""Ideal inverting integrator and explicit leaky-integrator extension."""
import math


def constant_input(r, c, vin, initial, time):
    if r <= 0 or c <= 0 or time < 0:
        raise ValueError('Invalid integration parameters')
    return initial - vin * time / (r * c)


def piecewise_constant(r, c, initial, segments):
    out = initial
    for duration, vin in segments:
        out = constant_input(r, c, vin, out, duration)
    return out


def sinusoid(r, c, amplitude, omega, initial, time):
    if r <= 0 or c <= 0 or omega <= 0 or time < 0:
        raise ValueError('Invalid sinusoid parameters')
    return initial + amplitude * (math.cos(omega * time) - 1) / (omega * r * c)


def practical_response(r, c, rf, frequency):
    if min(r, c, rf) <= 0 or frequency < 0:
        raise ValueError('Invalid practical integrator parameters')
    return -(rf / r) / (1 + 2j * math.pi * frequency * rf * c)


def dc_rail_time(r, c, vin, initial, lower, upper):
    """Ideal time to first rail; says nothing about post-saturation recovery."""
    if not lower < initial < upper or r <= 0 or c <= 0:
        raise ValueError('Initial output must lie strictly inside rails')
    if vin == 0:
        return math.inf
    target = lower if vin > 0 else upper
    return (initial - target) * r * c / vin
