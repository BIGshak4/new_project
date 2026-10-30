"""One black-box modulo-16 counter plus one same-clock high state bit."""


def next_high(low_before_edge, high_before_edge, *, reset=False):
    if type(low_before_edge) is not int or not 0 <= low_before_edge < 16:
        raise ValueError("low output must be four unsigned bits")
    if type(high_before_edge) is not int or high_before_edge not in (0, 1):
        raise ValueError("high state must be one bit")
    return 0 if reset else high_before_edge ^ int(low_before_edge == 15)


class ExtendedCounter:
    """The supplied callback models the inaccessible low counter.

    Both updates sample OLD state at one edge. ``reset`` is permitted only under
    the explicit added contract that both the black box and high DFF initialize
    together; the screenshot did not specify that interface.
    """

    def __init__(self, low_step, low=0, high=0):
        next_high(low, high)
        self.low_step = low_step
        self.low, self.high = low, high

    @property
    def output(self):
        return (self.high << 4) | self.low

    def edge(self, *, reset=False):
        old_low, old_high = self.low, self.high
        self.high = next_high(old_low, old_high, reset=reset)
        self.low = self.low_step(old_low, reset)
        return self.output
