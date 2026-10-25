"""Five simultaneous input bits to a three-bit population count, using three FAs.

Only FA primitives, free zero, wiring and fanout are hardware resources.
Python shifts/arithmetic encode or inspect wires; they are not extra circuit cells.
"""


def full_adder(a, b, c):
    if any(type(x) is not int or x not in (0, 1) for x in (a, b, c)):
        raise ValueError("FA inputs must be binary integers")
    return a ^ b ^ c, (a & b) | (a & c) | (b & c)


def network(value):
    if type(value) is not int or not 0 <= value < 32:
        raise ValueError("five-bit unsigned input required")
    x = [(value >> bit) & 1 for bit in range(5)]
    s1, c1 = full_adder(x[0], x[1], x[2])
    y0, c2 = full_adder(s1, x[3], x[4])
    y1, y2 = full_adder(c1, c2, 0)
    return {"x": x, "s1": s1, "c1": c1, "c2": c2, "y0": y0, "y1": y1, "y2": y2}


def popcount5(value):
    wires = network(value)
    return wires["y0"] + 2 * wires["y1"] + 4 * wires["y2"]
