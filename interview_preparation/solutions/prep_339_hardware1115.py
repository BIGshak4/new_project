"""State order follows the printed S0,S1,S2 order."""


def step(state):
    if len(state) != 3 or any(bit not in (0, 1) for bit in state):
        raise ValueError("three binary stages are required")
    s0, s1, s2 = state
    return s1 ^ s2, s0, s1


def trace(edges, initial=(0, 0, 1)):
    if edges < 0:
        raise ValueError("nonnegative edge count required")
    state = tuple(initial)
    rows = [(0, state, state[2])]
    for edge in range(1, edges + 1):
        state = step(state)
        rows.append((edge, state, state[2]))
    return rows
