"""Ideal stable-phase Boolean models, not a physical MUX-loop implementation."""
from dataclasses import dataclass


def latch(q: int, data: int, enable: int) -> int:
    if any(value not in (0, 1) for value in (q, data, enable)):
        raise ValueError("binary values required")
    return data if enable else q


@dataclass
class MasterSlave:
    """After phase settling: master open low, slave open high.

    Data must be stable through the low-to-high transition. No analogue delay,
    metastability, clock overlap, reset or unknown-state model is included.
    """

    master: int = 0
    q: int = 0

    def settle(self, data: int, clock: int) -> int:
        if clock not in (0, 1) or data not in (0, 1):
            raise ValueError("binary values required")
        if clock == 0:
            self.master = latch(self.master, data, 1)
        else:
            self.q = latch(self.q, self.master, 1)
        return self.q


def register_enabled(q: int, data: int, enable: int, width: int) -> int:
    """State at a rising edge for a W-bit register with synchronous enable."""
    if width < 1 or enable not in (0, 1):
        raise ValueError("positive width and binary enable required")
    if not (0 <= q < 1 << width and 0 <= data < 1 << width):
        raise ValueError("unsigned data must fit width")
    return data if enable else q
