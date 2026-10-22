"""Exact ray parity for a supplied simple polygon; no simplicity validator.

Vertices must be ordered, distinct at consecutive positions, and must describe
a simple polygon with at least three vertices. Do not repeat the first vertex
at the end. Integer coordinates use Python's arbitrary precision arithmetic.
The caller, not this O(n) routine, guarantees simplicity. A crossing input is
outside the advertised contract; the parity calculation is not a validator.
"""

from collections.abc import Sequence

Point = tuple[int, int]


def orientation(a: Point, b: Point, p: Point) -> int:
    """Signed twice-area, evaluated exactly for integer coordinates."""
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def point_in_polygon(vertices: Sequence[Point], p: Point) -> str:
    """Return 'inside', 'outside', or 'boundary' under the module contract.

    O(n) arithmetic operations, O(1) auxiliary integer variables. Integer bit
    lengths affect the cost of multiplication and memory; neither floats nor
    an epsilon are used. Boundary support is a helper beyond the screenshot's
    promise that p lies on no edge's supporting line.
    """
    if len(vertices) < 3:
        raise ValueError("at least three ordered polygon vertices are required")
    if len(p) != 2 or any(type(c) is not int for c in p):
        raise ValueError("query coordinates must be integers")
    inside = False
    px, py = p
    for i, a in enumerate(vertices):
        b = vertices[(i + 1) % len(vertices)]
        if len(a) != 2 or len(b) != 2 or any(type(c) is not int for c in (*a, *b)):
            raise ValueError("vertex coordinates must be integers")
        if a == b:
            raise ValueError("zero-length edges are outside the contract")
        cross = orientation(a, b, p)
        if (cross == 0 and min(a[0], b[0]) <= px <= max(a[0], b[0])
                and min(a[1], b[1]) <= py <= max(a[1], b[1])):
            return "boundary"
        # Half-open y intervals make a vertex hit obey the same parity rule.
        # x_intersection - px == cross / (b.y - a.y).
        if (a[1] > py) != (b[1] > py) and (cross > 0) == (b[1] > a[1]):
            inside = not inside
    return "inside" if inside else "outside"
