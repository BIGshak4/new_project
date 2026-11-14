"""Sampled controller for a three-floor educational model. Floor IDs are 0..2."""

class Elevator:
    def __init__(self):
        self.state = "idle"
        self.pending = 0
        self.target = 0
        self.last = 2

    def motor(self, floor, closed):
        if self.state != "travel" or not closed:
            return 0
        return (self.target > floor) - (self.target < floor)

    def tick(self, floor, closed, opened, cabin=0, hall=0):
        self.pending |= cabin | hall
        if self.state == "idle" and closed and self.pending:
            order = [(self.last + step) % 3 for step in (1, 2, 3)]
            self.target = next(f for f in order if self.pending & (1 << f))
            self.state = "opening" if floor == self.target else "travel"
        elif self.state == "travel" and floor == self.target:
            self.state = "opening"
        elif self.state == "opening" and opened:
            self.pending &= ~(1 << self.target)
            self.last = self.target
            self.state = "open"
        elif self.state == "open":
            self.state = "closing"
        elif self.state == "closing" and closed:
            self.state = "idle"
        return self.state

