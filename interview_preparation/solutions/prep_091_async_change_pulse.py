"""Ideal event model: asynchronous XOR pulse until the next rising edge.

Input changes exactly at a sampling edge are deliberately outside this model.
Initial sampled state must be supplied; no reset is implied by the source.
"""
from dataclasses import dataclass


@dataclass
class ChangePulse:
    sampled: int = 0
    data: int = 0

    @property
    def out(self) -> int:
        return self.data ^ self.sampled

    def input_change(self, value: int) -> int:
        if value not in (0, 1):
            raise ValueError("binary input required")
        self.data = value
        return self.out

    def rising_edge(self) -> int:
        self.sampled = self.data
        return self.out
