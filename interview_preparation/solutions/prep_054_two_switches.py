"""PREP-054: 17 prisoners, TWO switches, exactly ONE toggle on EVERY visit.

Prisoner 0 is the counter. Switch S carries tokens. Switch D is a dummy.
Both switches may initially have either state. Local memories start at zero.
The simulator contains all memories only for checking; each real prisoner needs
only their own memory and the visible switches. Fair visitation is required.
"""
from dataclasses import dataclass, field


@dataclass
class TwoSwitchProtocol:
    n: int = 17
    signal: bool = False
    dummy: bool = False
    contributions: list[int] = field(default_factory=list)
    observed: int = 0

    def __post_init__(self):
        if self.n < 2:
            raise ValueError("At least two prisoners are required")
        if not self.contributions:
            self.contributions = [0] * self.n

    @property
    def threshold(self):
        return 2 * (self.n - 1)

    def visit(self, prisoner: int) -> tuple[str, bool]:
        if not 0 <= prisoner < self.n:
            raise ValueError("Unknown prisoner")
        if self.observed >= self.threshold:
            raise RuntimeError("The protocol has already declared success")
        if prisoner == 0 and self.signal:
            self.signal = False
            self.observed += 1
            action = "S: ON -> OFF"
        elif prisoner != 0 and not self.signal and self.contributions[prisoner] < 2:
            self.signal = True
            self.contributions[prisoner] += 1
            action = "S: OFF -> ON"
        else:
            self.dummy = not self.dummy
            action = "D: toggle"
        return action, self.observed == self.threshold


if __name__ == "__main__":
    protocol = TwoSwitchProtocol(signal=True, dummy=True)
    # Deterministic fair schedule for demonstration, not a claimed time bound.
    done = False
    while not done:
        for p in range(protocol.n):
            action, done = protocol.visit(p)
            if done:
                print("All 17 have visited; counter observed", protocol.observed)
                break
