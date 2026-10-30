"""Mealy event from OLD prefix state and current accepted bit, before update."""

TABLE = {
    0: {0: (0, 0), 1: (1, 0)},
    1: {0: (2, 0), 1: (1, 0)},
    2: {0: (0, 0), 1: (3, 0)},
    3: {0: (2, 0), 1: (1, 1)},
}


def step(state, bit, *, reset=False):
    if type(state) is not int or state not in TABLE or type(bit) is not int or bit not in (0, 1):
        raise ValueError("valid prefix state and binary input required")
    return (0, 0) if reset else TABLE[state][bit]


def detections(bits):
    state = 0
    outputs = []
    for bit in bits:
        state, event = step(state, bit)
        outputs.append(event)
    return outputs
