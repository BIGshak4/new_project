"""Overlapping Moore detector; state is the longest matched prefix length."""

TRANSITIONS = ((0, 1), (0, 2), (3, 2), (0, 4), (0, 2))


def detect(bits, resets=()):
    state = 0
    reset_edges = set(resets)
    output = []
    for edge, bit in enumerate(bits):
        if bit not in (0, 1):
            raise ValueError("bits must be binary")
        state = 0 if edge in reset_edges else TRANSITIONS[state][bit]
        output.append(int(state == 4))
    return output
