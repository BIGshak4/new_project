"""Two explicitly distinct readings of the source's ambiguous prime marks."""


def mux(select, d0, d1):
    return d1 if select else d0


def complemented_product(a, b, c):
    inner = mux(b, 1, c)
    return mux(a, 1, inner)  # NOT(a AND b AND NOT(c))


def plain_product(a, b, c):
    inner = mux(c, b, 0)
    return mux(a, 0, inner)  # a AND b AND NOT(c)
