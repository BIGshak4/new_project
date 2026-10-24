"""Eight-FA steady-state model for unsigned 8-bit input and full 11-bit output.

Shifts, fanout and constant-zero connections represent wiring, not extra gates.
The model is not an HDL simulation, synthesis result or physical timing result.
"""


def full_adder(a, b, carry_in):
    return a ^ b ^ carry_in, (a & b) | (a & carry_in) | (b & carry_in)


def times_six(value, *, with_trace=False):
    if type(value) is not int or not 0 <= value <= 255:
        raise ValueError("value must be an unsigned 8-bit integer")
    output = (value & 1) << 1  # y0=0, y1=a0: fixed wiring.
    carry = 0
    trace = []
    for column in range(2, 10):
        a = (value >> (column - 1)) & 1 if column <= 8 else 0
        b = (value >> (column - 2)) & 1
        bit, carry_out = full_adder(a, b, carry)
        trace.append({"column": column, "a": a, "b": b,
                      "carry_in": carry, "sum": bit, "carry_out": carry_out})
        output |= bit << column
        carry = carry_out
    output |= carry << 10
    return (output, trace) if with_trace else output
