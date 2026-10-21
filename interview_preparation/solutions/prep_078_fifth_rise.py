"""Synchronous sampled-input edge detector and modulo-five event counter."""
from dataclasses import dataclass


@dataclass
class EveryFifthRise:
    previous: int = 0
    count: int = 0
    pulse: int = 0

    def tick(self, signal: int, reset: bool = False) -> int:
        if signal not in (0, 1):
            raise ValueError("signal must be a sampled binary value")
        if reset:
            self.previous = self.count = self.pulse = 0
            return 0
        event = signal == 1 and self.previous == 0
        self.previous = signal
        self.pulse = int(event and self.count == 4)
        if event:
            self.count = 0 if self.count == 4 else self.count + 1
        return self.pulse
