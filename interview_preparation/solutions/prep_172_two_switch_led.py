"""Settled binary switch logic, not debounce, transient or device verification."""


def bit(value):
    if type(value) is not int or value not in (0, 1):
        raise ValueError("one integer bit required")
    return value


def xor_led(first, second):
    return bit(first) ^ bit(second)


def traveler_path(first, second):
    """Two SPDT switches select the same traveler => complete low-voltage path."""
    return int(bit(first) == bit(second))


def current_limit(supply, forward_drop, target_current, driver_drop=0.0):
    if target_current <= 0 or supply <= forward_drop + driver_drop:
        raise ValueError("positive headroom and current required")
    return (supply - forward_drop - driver_drop) / target_current
