"""Exactly one unpaired integer; every other value has even multiplicity.

The source's pair-only promise is stronger than needed. Array termination or
length must still be provided; an unknown n is not an unbounded raw pointer.
"""


def unpaired_value(values):
    answer = 0
    for value in values:
        answer ^= value
    return answer
