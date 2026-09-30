"""Implement f=NOT(a AND b AND NOT c) using ordinary non-inverting 2:1 MUXes."""


def mux(s, i0, i1):
    return i1 if s else i0


def part_a(a, b, c):
    not_b = mux(b, 1, 0)
    not_ab = mux(a, 1, not_b)
    return mux(c, not_ab, 1)


def part_b(a, b, c):
    inner = mux(b, 1, c)
    return mux(a, 1, inner)
