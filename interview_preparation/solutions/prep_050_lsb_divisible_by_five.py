"""Five-state LSB-first divisibility detector; Python functional model.

The state is a normalized residue, NOT the ordinary numeric remainder.
Empty input denotes zero. Call reset between independent words.
"""

from dataclasses import dataclass

TRANSITIONS = ((0, 3), (3, 1), (1, 4), (4, 2), (2, 0))


def advance(state: int, bit: int) -> int:
    if type(state) is not int or not 0 <= state < 5:
        raise ValueError("state must be an integer from 0 through 4")
    if type(bit) is not int or bit not in (0, 1):
        raise ValueError("bit must be integer zero or one")
    return TRANSITIONS[state][bit]


@dataclass
class DivisibleByFiveLSB:
    state: int = 0

    @property
    def divisible(self) -> bool:
        return self.state == 0

    def tick(self, bit: int = 0, *, valid: bool = True, reset: bool = False) -> bool:
        """One rising edge. Reset has priority; invalid cycles hold state."""
        if reset:
            self.state = 0
        elif valid:
            self.state = advance(self.state, bit)
        return self.divisible


def divisible_lsb(bits: list[int]) -> bool:
    detector = DivisibleByFiveLSB()
    for bit in bits:
        detector.tick(bit)
    return detector.divisible


if __name__ == "__main__":
    # LSB first: 1,0,0,1,1 represents 1+8+16 = 25.
    assert divisible_lsb([1, 0, 0, 1, 1])
    assert not divisible_lsb([1, 1, 0, 0, 1])  # 19
