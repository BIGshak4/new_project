"""Registered one-period pulse after every third nonreset rising edge."""


class EveryThirdClock:
    def __init__(self):
        self.count = 0
        self.pulse = 0

    def step(self, reset: bool = False) -> int:
        if reset:
            self.count = 0
            self.pulse = 0
        elif self.count == 2:
            self.count = 0
            self.pulse = 1
        else:
            self.count += 1
            self.pulse = 0
        return self.pulse
