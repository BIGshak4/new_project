"""Longest ones run in an array; inclusive endpoints, earliest tie."""


def longest_ones(bits):
    if type(bits) is not list or any(type(bit) is not int or bit not in (0, 1) for bit in bits):
        raise ValueError("a list of integer bits is required")
    current_start = 0
    current_length = 0
    best_start = best_end = -1
    best_length = 0
    for index, bit in enumerate(bits):
        if bit == 0:
            current_length = 0
        else:
            if current_length == 0:
                current_start = index
            current_length += 1
            if current_length > best_length:
                best_start, best_end = current_start, index
                best_length = current_length
    return [best_start, best_end]
