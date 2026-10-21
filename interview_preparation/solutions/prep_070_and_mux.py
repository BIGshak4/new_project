"""AND using one ideal MUX2:1 and an allowed constant zero."""


def mux(s: int, d0: int, d1: int) -> int:
    if any(type(v) is not int or v not in (0, 1) for v in (s, d0, d1)):
        raise ValueError("binary integer inputs required")
    return d1 if s else d0


def and_from_mux(a: int, b: int) -> int:
    return mux(a, 0, b)
