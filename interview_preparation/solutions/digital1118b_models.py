"""DC feedback example and a fixed-width two-register teaching machine."""


def open_loop(vplus, vminus, gain, low, high):
    return min(high, max(low, gain * (vplus - vminus)))


def follower(vin, gain, low, high):
    return min(high, max(low, gain * vin / (1 + gain)))


def copy_instructions(width):
    """Generate (opcode, register, [branch target]) tuples for two w-bit registers.

    JMPZ examines the named register. INC/DEC have their ordinary meaning.
    A branch to the end of the instruction list finishes the computation.
    """
    if width < 1:
        raise ValueError("width must be positive")
    largest = (1 << width) - 1
    instructions = []
    count_start = 2 * largest
    restore_start = 4 * largest
    end = restore_start + 2 * largest

    for _ in range(largest):
        instructions.extend([("JMPZ", 1, count_start), ("DEC", 1)])
    for consumed in range(largest):
        instructions.extend([("JMPZ", 0, end - 2 * consumed), ("DEC", 0)])
    for _ in range(largest):
        instructions.extend([("INC", 0), ("INC", 1)])
    return instructions
