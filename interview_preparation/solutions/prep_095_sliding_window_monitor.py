"""Sampled-cycle reference monitor and offline DUT checker for PREP-095.

Logical sample x[n] belongs to cycle n; y[n] is observed after DUT settling.
The default contract is zero same-cycle latency and zero-padded reset history.
No simulator, hardware interface or timing-aperture validation is performed.
"""
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class WindowMonitor:
    history: int = 0

    def reset(self) -> None:
        self.history = 0

    def sample(self, x: int) -> int:
        if x not in (0, 1):
            raise ValueError("binary sample required")
        self.history = ((self.history << 1) | x) & 0x3FF
        return int(self.history.bit_count() >= 3)


def check_samples(xs: Sequence[int], ys: Sequence[int]) -> list[int]:
    """Return zero-based failing cycle indexes; length mismatch is an error."""
    if len(xs) != len(ys):
        raise ValueError("one observed Y is required per sampled X")
    monitor = WindowMonitor()
    return [i for i, (x, y) in enumerate(zip(xs, ys, strict=True))
            if monitor.sample(x) != y]
