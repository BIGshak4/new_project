"""Gate-only stable two-state MUX construction with constants 0 and 1 allowed."""


def bit(value):
    if type(value) is not int or value not in (0, 1):
        raise ValueError("expected integer bit")
    return value


def mux(select, data0, data1):
    select, data0, data1 = map(bit, (select, data0, data1))
    return ((select ^ 1) & data0) | (select & data1)


def nand_nor(a, b):
    """Return (NAND, NOR); three MUXes share the complemented B signal."""
    a, b = bit(a), bit(b)
    not_b = mux(b, 1, 0)
    return mux(a, 1, not_b), mux(a, not_b, 0)
