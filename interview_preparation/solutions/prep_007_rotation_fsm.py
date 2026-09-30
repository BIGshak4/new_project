"""Ideal two-sensor direction decoder for the orientation in PREP-007.

A is above B on the lower-left rim; black=1. Every sensor transition
must be observed. This is an event/sampling model, not physical HDL.
"""


def classify(previous, current):
    """AB is encoded as (A << 1) | B. No memory is updated here."""
    if previous not in range(4) or current not in range(4):
        raise ValueError("AB must be 0, 1, 2 or 3")
    changed = previous ^ current
    if changed == 0:
        return "NO_CHANGE"
    if changed == 3:
        return "INVALID"
    previous_a = (previous >> 1) & 1
    current_b = current & 1
    return "CW" if previous_a ^ current_b else "CCW"


class RotationFSM:
    def __init__(self):
        self.previous = None

    def step(self, a, b):
        if a not in (0, 1) or b not in (0, 1):
            raise ValueError("Sensor readings must be binary")
        current = (a << 1) | b
        result = "UNKNOWN" if self.previous is None else classify(self.previous, current)
        # For an invalid jump, resynchronize without claiming a direction.
        self.previous = current
        return result
