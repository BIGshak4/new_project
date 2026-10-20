"""PREP-057: 21 prisoners; one optional light, unknown initial state.

Prisoner 0 counts. Each other prisoner may turn OFF->ON twice in total.
Unproductive visitors leave the light unchanged. Fair visitation is essential.
"""
from dataclasses import dataclass, field


@dataclass
class OneLightProtocol:
    n: int = 21
    light: bool = False
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
        if prisoner == 0 and self.light:
            self.light = False
            self.observed += 1
            action = "ON -> OFF"
        elif prisoner != 0 and not self.light and self.contributions[prisoner] < 2:
            self.light = True
            self.contributions[prisoner] += 1
            action = "OFF -> ON"
        else:
            action = "leave unchanged"
        return action, self.observed == self.threshold


if __name__ == "__main__":
    protocol = OneLightProtocol(light=True)
    done = False
    while not done:
        for p in range(protocol.n):
            action, done = protocol.visit(p)
            if done:
                print("All 21 have visited; counter observed", protocol.observed)
                break
