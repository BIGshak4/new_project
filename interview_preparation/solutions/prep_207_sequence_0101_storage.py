"""Moore FSM and explicitly stateful four-tap rolling FIFO abstraction."""

from collections import deque

TRANSITIONS = ((1, 0), (1, 2), (3, 0), (1, 4), (3, 0))


def detect_moore(bits, resets=()):
    state = 0
    reset_edges = set(resets)
    result = []
    for edge, bit in enumerate(bits):
        if bit not in (0, 1):
            raise ValueError("binary serial input required")
        state = 0 if edge in reset_edges else TRANSITIONS[state][bit]
        result.append(int(state == 4))
    return result


def detect_rolling_fifo(bits, resets=()):
    # Requires a rolling overwrite policy and simultaneous four-entry peek.
    # These are extra contracts, not properties of every ordinary FIFO IP.
    history = deque(maxlen=4)
    reset_edges = set(resets)
    result = []
    for edge, bit in enumerate(bits):
        if bit not in (0, 1):
            raise ValueError("DIN is the current serial input bit, not a constant")
        if edge in reset_edges:
            history.clear()
        else:
            history.append(bit)
        result.append(int(len(history) == 4 and tuple(history) == (0, 1, 0, 1)))
    return result
