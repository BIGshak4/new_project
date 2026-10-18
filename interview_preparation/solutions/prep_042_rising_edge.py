"""Registered one-cycle rising-edge detector for a synchronous binary input."""


class RisingEdgeDetector:
    def __init__(self, initial_previous: int = 0):
        if initial_previous not in (0, 1):
            raise ValueError("Initial sample must be a bit")
        self.previous = initial_previous
        self.pulse = 0

    def step(self, current: int, reset: bool = False) -> int:
        if current not in (0, 1):
            raise ValueError("Input must be a bit")
        if reset:
            self.previous = 0
            self.pulse = 0
        else:
            self.pulse = current & (1 - self.previous)
            self.previous = current
        return self.pulse
