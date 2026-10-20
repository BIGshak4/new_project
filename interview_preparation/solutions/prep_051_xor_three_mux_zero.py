"""Three-input XOR using only 2:1 MUX instances and constant zero.

mux(s,d0,d1) selects d0 for s=0, d1 for s=1. No hidden NOT/one.
"""

NETLIST = (
    ("t", "B", "A", "0"),
    ("P", "A", "B", "t"),
    ("u", "C", "P", "0"),
    ("F", "P", "C", "u"),
)


def mux(s: int, d0: int, d1: int) -> int:
    return d1 if s else d0


def xor_three(A: int, B: int, C: int) -> int:
    if any(type(value) is not int or value not in (0, 1) for value in (A, B, C)):
        raise ValueError("inputs must be integer bits")
    wires = {"A": A, "B": B, "C": C, "0": 0}
    for out, select, d0, d1 in NETLIST:
        wires[out] = mux(wires[select], wires[d0], wires[d1])
    return wires["F"]


if __name__ == "__main__":
    for A in (0, 1):
        for B in (0, 1):
            for C in (0, 1):
                print(A, B, C, "->", xor_three(A, B, C))
