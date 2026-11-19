"""Counter result is latched on the first low sample after a run of highs."""

class PulseMeter:
    def __init__(self):
        self.count = 0
        self.clipped = False
        self.result = 0
        self.overflow = False

    def tick(self, high, reset=False):
        if reset:
            self.__init__()
            return False
        if high:
            if self.count == 255:
                self.clipped = True
            else:
                self.count += 1
            return False
        if not self.count:
            return False
        self.result, self.overflow = self.count, self.clipped
        self.count, self.clipped = 0, False
        return True

