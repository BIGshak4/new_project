"""Four binary DATA lines: one-use alphabet and framed two-use extension."""


def encode16(symbol: int) -> int:
    if not 0 <= symbol < 16:
        raise ValueError("one four-bit transfer encodes only symbols 0..15")
    return symbol


def encode18(symbol: int) -> tuple[int, int]:
    if not 0 <= symbol < 18:
        raise ValueError("symbol must lie in 0..17")
    return symbol & 15, symbol >> 4


def decode18(first: int, second: int) -> int:
    if not 0 <= first < 16 or not 0 <= second < 16:
        raise ValueError("each transfer has exactly four binary DATA bits")
    symbol = first | (second << 4)
    if symbol >= 18:
        raise ValueError("unassigned two-transfer word")
    return symbol
