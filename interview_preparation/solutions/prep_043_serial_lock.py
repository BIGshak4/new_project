"""ABCD sequence recognition, with prefix fallback and an optional persistent lock."""


def transition(state: int, symbol: str) -> tuple[int, int]:
    if state not in range(4) or not isinstance(symbol, str) or len(symbol) != 1:
        raise ValueError("Require prefix state 0..3 and one input character")
    detected = int(state == 3 and symbol == "D")
    if symbol == "A":
        following = 1
    elif state == 1 and symbol == "B":
        following = 2
    elif state == 2 and symbol == "C":
        following = 3
    else:
        following = 0
    return following, detected


class SequenceDetector:
    def __init__(self):
        self.state = 0

    def step(self, symbol: str, reset: bool = False) -> int:
        if reset:
            self.state = 0
            return 0
        self.state, pulse = transition(self.state, symbol)
        return pulse


class PersistentLock:
    def __init__(self):
        self.detector = SequenceDetector()
        self.opened = False

    def step(self, symbol: str, reset: bool = False) -> int:
        if reset:
            self.detector.step(symbol, reset=True)
            self.opened = False
        elif not self.opened:
            self.opened = bool(self.detector.step(symbol))
        return int(self.opened)
