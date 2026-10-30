"""Four-symbol prefix machine; all eight 3-bit codes, repeated targets allowed."""


class FourSymbolDetector:
    def __init__(self, target):
        if len(target) != 4 or any(type(x) is not int or not 0 <= x < 8 for x in target):
            raise ValueError("four 3-bit target symbols required")
        self.target = tuple(target)
        self.state = 0
        self.table = {}
        for state in range(5):
            for symbol in range(8):
                candidate = self.target[:state] + (symbol,)
                self.table[state, symbol] = max(
                    length for length in range(5)
                    if length <= len(candidate)
                    and (length == 0 or candidate[-length:] == self.target[:length])
                )

    def step(self, symbol, reset=False):
        if type(symbol) is not int or not 0 <= symbol < 8:
            raise ValueError("3-bit input symbol required")
        self.state = 0 if reset else self.table[self.state, symbol]
        return int(self.state == 4)
