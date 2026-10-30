"""HA using XOR/AND; FA using three HAs, with no outside OR gate."""


def half_adder(a, b):
    if any(type(x) is not int or x not in (0, 1) for x in (a, b)):
        raise ValueError("binary inputs required")
    return a ^ b, a & b


def full_adder(a, b, carry_in):
    p, g = half_adder(a, b)
    total_bit, h = half_adder(p, carry_in)
    carry_out, impossible_carry = half_adder(g, h)
    assert impossible_carry == 0  # g and h are mutually exclusive
    return total_bit, carry_out
