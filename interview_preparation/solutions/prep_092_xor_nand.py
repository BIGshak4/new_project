"""Four two-input Boolean NAND gates; ideal steady-state truth values only."""


def nand(a: bool, b: bool) -> bool:
    return not (a and b)


def xor_from_nand(a: bool, b: bool) -> bool:
    shared = nand(a, b)
    left = nand(a, shared)
    right = nand(b, shared)
    return nand(left, right)
