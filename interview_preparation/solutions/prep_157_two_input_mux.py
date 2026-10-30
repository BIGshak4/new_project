"""Ideal one-bit 2:1 MUX, selector zero chooses D0."""


def mux(d0, d1, select):
    if any(value not in (0, 1) for value in (d0, d1, select)):
        raise ValueError('Expected binary levels')
    return ((1 - select) & d0) | (select & d1)
