"""Executable arithmetic models; two distinct scalar storage locations.

The returned tuple is the test harness's observation, not a third persistent
value used by the swap algorithm. Python integers have arbitrary precision.
"""


def swap_exact(a: int, b: int) -> tuple[int, int]:
    a = a + b
    b = a - b
    a = a - b
    return a, b


def swap_u8_xor(a: int, b: int) -> tuple[int, int]:
    if type(a) is not int or type(b) is not int or not 0 <= a < 256 or not 0 <= b < 256:
        raise ValueError("expected two unsigned bytes")
    a ^= b
    b ^= a
    a ^= b
    return a, b


def swap_u8_modular(a: int, b: int) -> tuple[int, int]:
    if type(a) is not int or type(b) is not int or not 0 <= a < 256 or not 0 <= b < 256:
        raise ValueError("expected two unsigned bytes")
    a = (a + b) & 255
    b = (a - b) & 255
    a = (a - b) & 255
    return a, b


def swap_locations(cells: list[int], first: int, second: int) -> None:
    """Aliasing-safe illustration. Indices are caller-provided, not value temps."""
    if first == second:
        return
    cells[first] ^= cells[second]
    cells[second] ^= cells[first]
    cells[first] ^= cells[second]
