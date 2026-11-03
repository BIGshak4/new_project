"""Thought experiment only: no real device is released or building measured."""
import math


def height_from_fall_time(time, gravity=9.81):
    if not math.isfinite(time) or not math.isfinite(gravity) or time < 0 or gravity <= 0:
        raise ValueError('Finite time >= 0 and gravity > 0 required')
    return 0.5 * gravity * time * time


def height_interval(time, timing_error, gravity=9.81):
    if not math.isfinite(timing_error) or timing_error < 0:
        raise ValueError('Finite nonnegative timing error required')
    height_from_fall_time(time, gravity)
    return (height_from_fall_time(max(0, time - timing_error), gravity),
            height_from_fall_time(time + timing_error, gravity))
