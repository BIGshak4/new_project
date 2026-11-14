"""Registered outputs after the sampling edge, in (rise, fall, toggle) order."""

class EdgeDetector:
    def __init__(self):
        self.prev = 0

    def tick(self, x, reset=False):
        if reset:
            self.prev = 0
            return (0, 0, 0)
        rise = x & (1 - self.prev)
        fall = (1 - x) & self.prev
        self.prev = x
        return (rise, fall, rise | fall)

