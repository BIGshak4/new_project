"""Exact unsigned four-bit plus four-bit addition with ten half-adder cells.

No external carry-in. The result has five bits. Only half_adder calls create
circuit logic; Python indexing/packing represents wires, not extra adder/OR cells.
"""


def half_adder(a, b):
    if any(type(x) is not int or x not in (0, 1) for x in (a, b)):
        raise ValueError("HA inputs must be binary integers")
    return a ^ b, a & b


def trace_add4(a, b):
    if any(type(x) is not int or not 0 <= x < 16 for x in (a, b)):
        raise ValueError("two unsigned four-bit inputs required")
    a0, b0 = a & 1, b & 1
    s0, carry = half_adder(a0, b0)
    rows = [{"bit": 0, "a": a0, "b": b0, "cin": 0, "sum": s0,
             "g": carry, "h": 0, "cout": carry, "discarded": 0, "ha_cells": 1}]
    for bit in range(1, 4):
        ai, bi, incoming = (a >> bit) & 1, (b >> bit) & 1, carry
        p, g = half_adder(ai, bi)
        si, h = half_adder(p, incoming)
        carry, unused = half_adder(g, h)
        rows.append({"bit": bit, "a": ai, "b": bi, "cin": incoming, "sum": si,
                     "g": g, "h": h, "cout": carry, "discarded": unused, "ha_cells": 3})
    return rows


def add4(a, b):
    rows = trace_add4(a, b)
    return sum(row["sum"] << row["bit"] for row in rows) + (rows[-1]["cout"] << 4)
