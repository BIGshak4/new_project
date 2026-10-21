"""Destructive memory address test. Accesses must complete before returning.

The test detects stable address aliasing, not an otherwise correct bijective
renaming of physical cells. It is not a complete March/retention memory test.
"""
from collections.abc import Callable


def test_address_aliases(
    read: Callable[[int], int],
    write: Callable[[int, int], None],
    size: int,
    width: int,
) -> bool:
    """Return False on a mismatch; overwrite all locations even when healthy.

    For every address bit, write its value replicated across the data word,
    then read ALL locations. Repeat with the complement. W may be less than
    the number of address bits. The size-one case still tests 0 and all ones.
    """
    if type(size) is not int or size < 1 or type(width) is not int or width < 1:
        raise ValueError("size and width must be positive integers")
    mask = (1 << width) - 1
    for bit in range(max(1, (size - 1).bit_length())):
        for invert in (0, 1):
            for address in range(size):
                expected = mask if (((address >> bit) & 1) ^ invert) else 0
                write(address, expected)
            for address in range(size):
                expected = mask if (((address >> bit) & 1) ^ invert) else 0
                if read(address) != expected:
                    return False
    return True
