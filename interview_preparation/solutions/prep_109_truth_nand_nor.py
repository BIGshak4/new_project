"""Two-input, acyclic NAND/NOR networks; no free inverted inputs or constants."""

NAND_NETLIST = (("NAND", 1, 1), ("NAND", 0, 3), ("NAND", 2, 3), ("NAND", 4, 5))
NOR_NETLIST = (("NOR", 0, 2), ("NOR", 1, 3))


def evaluate(a, b, c, netlist):
    wires = [a, b, c]
    if any(type(value) is not int or value not in (0, 1) for value in wires):
        raise ValueError("A,B,C must be integer bits")
    for kind, left, right in netlist:
        if not 0 <= left < len(wires) or not 0 <= right < len(wires):
            raise ValueError("a gate must use existing wires")
        if kind == "NAND":
            value = 1 ^ (wires[left] & wires[right])
        elif kind == "NOR":
            value = 1 ^ (wires[left] | wires[right])
        else:
            raise ValueError("unsupported gate")
        wires.append(value)
    return wires[-1]
