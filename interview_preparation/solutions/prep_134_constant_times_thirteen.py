"""Two padded ripple-adder model for unsigned constant multiplication by 13.

Shifts by constants are wire placement after zero-extension to N+4 bits.
This is a functional Python cell model, not synthesized or timed circuitry.
"""


def full_adder(a, b, carry):
    return a ^ b ^ carry, (a & b) | (a & carry) | (b & carry)


def ripple(a, b, width):
    result, carry, trace = 0, 0, []
    for column in range(width):
        ai, bi = (a >> column) & 1, (b >> column) & 1
        bit, following = full_adder(ai, bi, carry)
        trace.append((ai, bi, carry, bit, following))
        result |= bit << column
        carry = following
    return result, carry, trace


def times_thirteen(value, width, *, with_trace=False):
    if type(width) is not int or width < 1:
        raise ValueError("input width must be a positive integer")
    if type(value) is not int or not 0 <= value < (1 << width):
        raise ValueError("input must fit its unsigned width")
    out_width = width + 4
    subtotal, carry1, trace1 = ripple(value << 3, value << 2, out_width)
    product, carry2, trace2 = ripple(subtotal, value, out_width)
    if carry1 or carry2:
        raise AssertionError("the N+4-bit bound must retain both intermediate sums")
    return (product, trace1, trace2) if with_trace else product
