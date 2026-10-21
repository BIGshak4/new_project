"""Fault is ONLY on C's NOR input branch, never on the inverter branch."""


def output(a: int, b: int, c: int, fault: int | None = None) -> int:
    if any(type(v) is not int or v not in (0, 1) for v in (a, b, c)):
        raise ValueError("binary integer inputs required")
    if fault is not None and (type(fault) is not int or fault not in (0, 1)):
        raise ValueError("fault must be None, 0 or 1")
    x = c if fault is None else fault
    return a & (1 - (b | x)) & (1 - c)
