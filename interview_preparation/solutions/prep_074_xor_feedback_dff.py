"""Edge-triggered XOR-feedback DFF model, not an analogue/HDL simulator."""
from __future__ import annotations


def next_q(q: int, a: int) -> int:
    if q not in (0, 1) or a not in (0, 1):
        raise ValueError("q and a must be bits")
    return q ^ a


def trace(q0: int, inputs: list[int]) -> list[int]:
    """Include initial Q, followed by Q after each rising edge."""
    if q0 not in (0, 1):
        raise ValueError("q0 must be a bit")
    states = [q0]
    for a in inputs:
        states.append(next_q(states[-1], a))
    return states


def delayed_events(q0: int, inputs: list[int], period: float, tcq: float) -> list[tuple[float, int]]:
    """Physical-Q transition times for a deliberately ideal constant-delay model.

    The first sampling edge is t=period; XOR is assumed settled before every
    sampling edge. This does not detect metastability or setup/hold violations.
    """
    if not 0 <= tcq < period:
        raise ValueError("require 0 <= tcq < period")
    states = trace(q0, inputs)
    return [((i + 1) * period + tcq, states[i + 1])
            for i in range(len(inputs)) if states[i + 1] != states[i]]


def feedback_timing_ok(period: float, tcq_max: float, xor_max: float,
                       setup: float, tcq_min: float, xor_min: float,
                       hold: float) -> bool:
    values = (period, tcq_max, xor_max, setup, tcq_min, xor_min, hold)
    if any(value < 0 for value in values) or tcq_min > tcq_max or xor_min > xor_max:
        raise ValueError("invalid delays")
    return period >= tcq_max + xor_max + setup and tcq_min + xor_min >= hold
