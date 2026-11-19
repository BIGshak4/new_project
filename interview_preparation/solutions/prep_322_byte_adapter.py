"""Two-bit synchronous link. 'tick' returns the word on valid transfer slots."""

class ByteAdapter:
    def __init__(self):
        self.slot = 0
        self.word = 0

    def tick(self, incoming=None):
        if self.slot == 0:
            if incoming is None or not 0 <= incoming <= 255:
                raise ValueError("an 8-bit word is required in slot zero")
            self.word = incoming
            pair = None
        else:
            if incoming is not None:
                raise ValueError("unexpected source word")
            shift = 2 * (4 - self.slot)
            pair = (self.word >> shift) & 3
        self.slot = (self.slot + 1) % 5
        return pair

