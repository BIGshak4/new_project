"""Two-state gates and most-significant-first unsigned comparator cascade."""


def compare_bit(a, b):
    if any(type(v) is not int or v not in (0, 1) for v in (a, b)):
        raise ValueError("expected integer bits")
    return a & (b ^ 1), (a ^ b) ^ 1, (a ^ 1) & b


def compare_words(a, b, width=4):
    if type(width) is not int or width < 1:
        raise ValueError("positive width required")
    if any(type(v) is not int or not 0 <= v < (1 << width) for v in (a, b)):
        raise ValueError("unsigned words outside width")
    greater, equal, less = 0, 1, 0
    for i in range(width - 1, -1, -1):
        gi, ei, li = compare_bit((a >> i) & 1, (b >> i) & 1)
        greater, less = greater | (equal & gi), less | (equal & li)
        equal &= ei
    return greater, equal, less
