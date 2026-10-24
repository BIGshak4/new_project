"""Two-state, rising-edge TFF model; the added XOR computes T=D XOR Q.

Clock, data and the feedback path must satisfy the primitive's timing contract.
No reset, initialized power-up state or physical metastability model is implied.
"""


def bit(value):
    if type(value) is not int or value not in (0, 1):
        raise ValueError("expected integer bit 0 or 1")
    return value


def tff(q, toggle, *, rising_edge=True):
    q, toggle = bit(q), bit(toggle)
    if type(rising_edge) is not bool:
        raise ValueError("rising_edge must be Boolean")
    return q ^ toggle if rising_edge else q


def dff_from_tff(q, data, *, rising_edge=True):
    q, data = bit(q), bit(data)
    toggle = data ^ q
    return tff(q, toggle, rising_edge=rising_edge)


def trace(data_samples, *, initial):
    q = bit(initial)
    states = []
    for data in data_samples:
        q = dff_from_tff(q, data)
        states.append(q)
    return states
