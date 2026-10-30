"""Check only a run closed by the next opposite bit, never an unfinished suffix."""

TABLE = {
    "ZO": {0: ("ZE", 0), 1: ("OO", 0)},
    "ZE": {0: ("ZO", 0), 1: ("OO", 1)},
    "OO": {0: ("ZO", 1), 1: ("OE", 0)},
    "OE": {0: ("ZO", 0), 1: ("OO", 0)},
}
RESET_STATE = "OE"  # Equivalent to an empty history for all future inputs.


def step(state, bit, *, reset=False):
    if state not in TABLE or type(bit) is not int or bit not in (0, 1):
        raise ValueError("valid run state and one integer bit required")
    return (RESET_STATE, 0) if reset else TABLE[state][bit]


def detect(bits):
    state = RESET_STATE
    outputs = []
    for bit in bits:
        state, error = step(state, bit)
        outputs.append(error)
    return outputs
