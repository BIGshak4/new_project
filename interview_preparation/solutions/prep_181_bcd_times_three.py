"""One valid BCD input digit, two BCD output digits; invalid input is flagged."""


def bcd_times_three(word):
    if type(word) is not int or not 0 <= word < 16:
        raise ValueError("four binary input bits required")
    valid = int(word < 10)
    if not valid:
        return 0, 0, 0
    product = (word << 1) + word  # six-bit binary product, at most 27
    if product >= 20:
        tens, ones = 2, product - 20
    elif product >= 10:
        tens, ones = 1, product - 10
    else:
        tens, ones = 0, product
    return valid, tens, ones
