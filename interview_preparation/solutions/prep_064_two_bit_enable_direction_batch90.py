"""Two-bit gate equations: inc enables counting, dec chooses its direction."""


def next_state(state, inc, dec, reset=0):
    if type(state) is not int or not 0 <= state < 4 or any(bit not in (0, 1) for bit in (inc, dec, reset)):
        raise ValueError("two-bit state and binary controls required")
    if reset:
        return 0
    q0, q1 = state & 1, (state >> 1) & 1
    toggle0 = inc
    toggle1 = inc & (q0 ^ dec)
    return ((q1 ^ toggle1) << 1) | (q0 ^ toggle0)
