"""Four-input >=3 threshold using exactly four >=2-of-4 A primitives.

Cost grammar: A gates only, free 0/1 constants, wires, fanout and tied pins;
no free inversion, other gates, feedback or storage.
"""


def threshold_a(a: int, b: int, c: int, d: int) -> int:
    """Behavioral model of the supplied primitive, not an extra circuit."""
    if any(bit not in (0, 1) for bit in (a, b, c, d)):
        raise ValueError("Each input must be a bit")
    return int(a + b + c + d >= 2)


def three_of_four(a: int, b: int, c: int, d: int) -> int:
    """A-only implementation; the target specification is sum(bits) >= 3."""
    p = threshold_a(c, d, 0, 0)
    q = threshold_a(c, d, 1, 0)
    r = threshold_a(a, b, p, 0)
    return threshold_a(r, q, 0, 0)


def netlist_values(a: int, b: int, c: int, d: int) -> tuple[int, int, int, int]:
    """Expose internal wires for truth-table and drawing verification."""
    p = threshold_a(c, d, 0, 0)
    q = threshold_a(c, d, 1, 0)
    r = threshold_a(a, b, p, 0)
    y = threshold_a(r, q, 0, 0)
    return p, q, r, y
