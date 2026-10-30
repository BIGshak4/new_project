"""Append-only () monitor; incoming tokens are chronological pushes.

No pop is part of this API. Ordinary characters, including other bracket
characters in this single-type extension, are ignored. Original mixed-type
stack validation remains a separate contract.
"""


class ParenthesisMonitor:
    def __init__(self):
        self.reset()

    def reset(self):
        self.depth, self.broken = 0, False

    @property
    def valid(self):
        return not self.broken and self.depth == 0

    def feed(self, symbol):
        if not isinstance(symbol, str) or len(symbol) != 1:
            raise ValueError("feed one character per append")
        if not self.broken:
            if symbol == "(":
                self.depth += 1
            elif symbol == ")":
                if self.depth == 0:
                    self.broken = True
                else:
                    self.depth -= 1
        return self.valid
