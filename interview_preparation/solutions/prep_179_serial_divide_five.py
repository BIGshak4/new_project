"""MSB-first long division; appending input b gives NUM' = 2*NUM+b.

The finite controller emits quotient bits. Python's unbounded quotient register
is an abstract observer, not a claim of physically infinite-width hardware.
"""


def step(remainder, bit):
    if type(remainder) is not int or not 0 <= remainder < 5:
        raise ValueError("remainder must be in 0..4")
    if type(bit) is not int or bit not in (0, 1):
        raise ValueError("one binary input required")
    trial = (remainder << 1) | bit
    quotient_bit = int(trial >= 5)
    return trial - 5 * quotient_bit, quotient_bit


def divide_stream(bits):
    remainder = quotient = 0
    trace = []
    for bit in bits:
        remainder, digit = step(remainder, bit)
        quotient = (quotient << 1) | digit
        trace.append((quotient, remainder, digit))
    return trace
