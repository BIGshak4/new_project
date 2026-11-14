"""Cycle-level model for a parallel-byte input and 8 processing clock edges."""

def divide_six(word):
    if not 0 <= word < 256:
        raise ValueError("an unsigned byte is required")
    remainder = 0
    quotient = 0
    for index in range(7, -1, -1):
        trial = 2 * remainder + ((word >> index) & 1)
        bit = int(trial >= 6)
        remainder = trial - 6 * bit
        quotient = (quotient << 1) | bit
    return quotient, remainder

