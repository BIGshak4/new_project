"""Three-bit enabled counter; reset and illegal-state recovery are explicit."""


def next_count(state, enable, reset=False):
    if not 0 <= state < 8 or enable not in (0, 1):
        raise ValueError("three-bit state and binary enable required")
    if reset or state >= 6:
        return 0
    if not enable:
        return state
    return 0 if state == 5 else state + 1
