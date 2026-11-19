"""Reference functions for the November 18 digital exercises."""


def square_step(index, square):
    """Compute the next state from the previous index and square."""
    return index + 1, square + (2 * index + 1)


def square_check(a, b, c):
    """Return (advances after operand capture, equal) for unsigned operands."""
    operands = (a, b, c)
    if any(type(x) is not int or x < 0 for x in operands):
        raise ValueError("nonnegative integer operands required")
    saved = [0, 0, 0]
    index, square = 0, 0
    end = max(operands)
    while True:
        for i, target in enumerate(operands):
            if target == index:
                saved[i] = square
        if index == end:
            return index, saved[0] + saved[1] == saved[2]
        index, square = square_step(index, square)


def p_drive(a, b):
    return 1 if (a, b) == (0, 0) else None


def n_drive(a, b):
    return 0 if (a, b) == (1, 1) else None


def resolve(drives):
    active = {value for value in drives if value is not None}
    if len(active) != 1:
        raise ValueError("floating output or opposing drivers")
    return active.pop()


def p_n_invert(x):
    return resolve((p_drive(x, x), n_drive(x, x)))


def p_n_nor(a, b):
    return resolve((p_drive(a, b), n_drive(a, a), n_drive(b, b)))


def nand_library(a, b):
    """Independent gate expressions, with sharing within each expression."""
    def nand(x, y):
        return 1 - x * y

    not_a, not_b = nand(a, a), nand(b, b)
    t = nand(a, b)
    disjunction = nand(not_a, not_b)
    return {
        "BUF": nand(not_a, not_a),
        "NOT": not_a,
        "AND": nand(t, t),
        "OR": disjunction,
        "NOR": nand(disjunction, disjunction),
        "XOR": nand(nand(a, t), nand(b, t)),
    }


def slacks_ps(period, cq_min, cq_max, d_min, d_max, setup, hold):
    return period - cq_max - d_max - setup, cq_min + d_min - hold


def count_7e_step(count, overflow, data, valid, reset, width):
    """Byte-aligned saturating count and sticky lost-match flag."""
    if reset:
        return 0, False
    maximum = (1 << width) - 1
    if valid and data == 0x7E:
        if count == maximum:
            return count, True
        return count + 1, overflow
    return count, overflow


def dissent(a, b, c):
    different_ab, different_ac = a ^ b, a ^ c
    different_bc = different_ab ^ different_ac
    return (
        different_ab | different_ac,
        (
            different_ab & different_ac,
            different_ab & different_bc,
            different_ac & different_bc,
        ),
    )


def expected_test_masks(size=64, cap=7):
    """Disjoint nonempty groups. A cap of zero cannot cover stuck-low cells."""
    if not 0 < cap < size:
        raise ValueError("require 0 < cap < size")
    return tuple(
        ((1 << min(cap, size - start)) - 1) << start
        for start in range(0, size, cap)
    )


def first_array_mismatch(write, read):
    """Destructive test. Return (round, expected, observed) or None."""
    for round_number, expected in enumerate(expected_test_masks(), start=1):
        write(expected)
        observed = read()
        if observed != expected:
            return round_number, expected, observed
    return None
