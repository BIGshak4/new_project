"""Finite exact character-stream controller; fourteen possible words."""


class DistinctWords:
    def __init__(self):
        self.reset()

    def reset(self):
        self.prefix = self.length = self.seen = self.count = 0
        self.error = self.done = False

    def accept(self, char, valid=True):
        if not valid or self.done:
            return
        if char in (" ", "\n"):
            if not self.error and self.length:
                index = (1 << self.length) - 2 + self.prefix
                mask = 1 << index
                if not self.seen & mask:
                    self.seen |= mask
                    self.count += 1
            self.prefix = self.length = 0
            if char == "\n":
                self.done = True
            return
        if self.error:
            return
        if char not in ("a", "b") or self.length == 3:
            self.error = True
            return
        self.prefix = 2*self.prefix + (char == "b")
        self.length += 1


def count_distinct(text):
    if not isinstance(text, str) or not text.endswith("\n") or text.count("\n") != 1:
        raise ValueError("one newline is required at the end of the input")
    unit = DistinctWords()
    for char in text:
        unit.accept(char)
    if not unit.done or unit.error:
        raise ValueError("valid newline-terminated bounded text required")
    return unit.count
