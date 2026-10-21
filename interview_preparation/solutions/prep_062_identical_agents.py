"""PREP-062: same local program; unit cost for EVERY executed primitive.

Model contract: common forward direction, simultaneous start, equal clocks,
integer separation in unit movement steps, static point markers, no obstacles.
IF_P guards only the next GOTO; false skips that GOTO without executing it.
A movement is linear during its unit interval; collision includes the interior
of an interval. The CPU never receives position, distance or the other CPU.
"""
from dataclasses import dataclass
from fractions import Fraction


PROGRAM_TEXT = """SLOW:
    MF
    if P:
        GOTO FAST
    GOTO SLOW
FAST:
    MF
    MF
    GOTO FAST
"""


@dataclass
class LocalCPU:
    pc: int = 0

    def tick(self, marker_here: bool) -> int:
        """Execute one primitive and return local displacement -1, 0 or +1."""
        if self.pc == 0:       # MF
            self.pc = 1
            return 1
        if self.pc == 1:       # if P (one tick, even when false)
            self.pc = 2 if marker_here else 3
        elif self.pc == 2:     # guarded GOTO FAST (a separate tick)
            self.pc = 4
        elif self.pc == 3:     # GOTO SLOW
            self.pc = 0
        elif self.pc == 4:     # first MF in FAST
            self.pc = 5
            return 1
        elif self.pc == 5:     # second MF in FAST
            self.pc = 6
            return 1
        elif self.pc == 6:     # GOTO FAST
            self.pc = 4
        else:
            raise ValueError("Invalid program counter")
        return 0


def simulate(separation, *, offset=0, directions=(1, 1), max_ticks=None):
    """Environment/test harness only; hidden global state is NOT given to CPUs.

    A noninteger distance can be supplied to demonstrate the model limitation.
    directions differing from (1,1) are outside the main common-direction model.
    """
    distance = Fraction(separation)
    positions = [Fraction(offset), Fraction(offset) + distance]
    markers = frozenset(positions)
    agents = [LocalCPU(), LocalCPU()]
    if positions[0] == positions[1]:
        return {"met": True, "time": Fraction(0), "marker_hits": []}
    if max_ticks is None:
        if distance.denominator != 1:
            raise ValueError("Provide a finite test bound for a noninteger distance")
        max_ticks = 6 * abs(int(distance)) + 10
    hits = []
    for start in range(max_ticks):
        visible = [p in markers for p in positions]
        for i in range(2):
            if agents[i].pc == 1 and visible[i]:
                hits.append((i, start + 1))
        moves = [agents[i].tick(visible[i]) * directions[i] for i in range(2)]
        gap = positions[1] - positions[0]
        closing = moves[0] - moves[1]
        if closing:
            fraction = gap / closing
            if 0 <= fraction <= 1:
                return {"met": True, "time": Fraction(start) + fraction, "marker_hits": hits}
        positions = [positions[i] + moves[i] for i in range(2)]
        if positions[0] == positions[1]:
            return {"met": True, "time": Fraction(start + 1), "marker_hits": hits}
    return {"met": False, "time": None, "marker_hits": hits}


if __name__ == "__main__":
    print(PROGRAM_TEXT)
    for d in (1, 2, 5, 10):
        result = simulate(d)
        print(f"D={d}: meet at t={result['time']}")
