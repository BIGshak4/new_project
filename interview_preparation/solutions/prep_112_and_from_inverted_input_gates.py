"""Explicit pin order: F(normal,inverted)=normal&~inverted;
G(normal,inverted)=normal|~inverted, for Boolean bits.
"""


def _bits(a, b):
    if any(type(v) is not int or v not in (0, 1) for v in (a, b)):
        raise ValueError("expected integer bits")


def andn(normal, inverted):
    _bits(normal, inverted)
    return normal & (inverted ^ 1)


def orn(normal, inverted):
    _bits(normal, inverted)
    return normal | (inverted ^ 1)


def both_with_zero(a, b):
    """One gate of each kind; a constant-zero wire is explicitly allowed."""
    return andn(a, orn(0, b))


def no_constants(a, b):
    """Two copies of ANDN; ORN unused; no constants."""
    return andn(a, andn(a, b))


def both_no_constants(a, b):
    """Three gates, uses both kinds; tied inputs allowed, no constant wires."""
    zero = andn(a, a)
    inverted_b = orn(zero, b)
    return andn(a, inverted_b)
