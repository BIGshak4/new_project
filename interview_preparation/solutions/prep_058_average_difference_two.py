"""Gate-equivalent average for unsigned N-bit a,b with b=a+2, no overflow.

Arithmetic used to validate the input contract is not a hardware datapath.
After validation, output bits use only bit selection, NOT/AND/OR equivalents.
"""


def average_gates(a: int, b: int, width: int) -> int:
    if type(width) is not int or width < 2:
        raise ValueError("width must be an integer >= 2")
    if any(type(value) is not int for value in (a, b)):
        raise ValueError("a,b must be integers")
    if not (0 <= a < (1 << width) and 0 <= b < (1 << width) and b == a + 2):
        raise ValueError("require unsigned N-bit a,b and exact b=a+2 without overflow")
    select = a & 1
    output = 1 ^ select
    for index in range(1, width):
        a_bit = (a >> index) & 1
        b_bit = (b >> index) & 1
        output |= (((1 ^ select) & a_bit) | (select & b_bit)) << index
    return output
