"""PREP-054 variant: YOU + 100 others = 101 prisoners, two visible lights.

Each visit must toggle one OR both lights. This strategy toggles exactly ONE,
which is an allowed subset. Signal S carries tokens; dummy D absorbs idle visits.
Known initial BOTH OFF: contributors send once, threshold 100.
Unknown initial lights: contributors send twice, threshold 200.
Private counters below are collected only for the test harness; actual visitors
read their own local memory and the two lights, never another person's memory.
"""
from dataclasses import dataclass, field


@dataclass
class Protocol101:
    known_both_off: bool = False
    signal: bool = False
    dummy: bool = False
    sent: list[int] = field(default_factory=lambda: [0] * 101)
    count: int = 0

    def __post_init__(self):
        if self.known_both_off and (self.signal or self.dummy):
            raise ValueError("Part A requires both lights initially OFF")

    @property
    def allowance(self):
        return 1 if self.known_both_off else 2

    @property
    def threshold(self):
        return 100 * self.allowance

    def visit(self, prisoner):
        if not 0 <= prisoner < 101:
            raise ValueError("Unknown prisoner")
        if self.count == self.threshold:
            raise RuntimeError("Declaration already made")
        if prisoner == 0 and self.signal:
            self.signal = False
            self.count += 1
            action = "S: ON -> OFF"
        elif prisoner != 0 and not self.signal and self.sent[prisoner] < self.allowance:
            self.signal = True
            self.sent[prisoner] += 1
            action = "S: OFF -> ON"
        else:
            self.dummy = not self.dummy
            action = "D: toggle"
        return action, self.count == self.threshold


if __name__ == "__main__":
    for known in (True, False):
        protocol = Protocol101(known_both_off=known)
        done = False
        while not done:
            for p in range(101):
                _, done = protocol.visit(p)
                if done:
                    print("known OFF:", known, "threshold:", protocol.count)
                    break
