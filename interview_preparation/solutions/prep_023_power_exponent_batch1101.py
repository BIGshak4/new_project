"""Return [is_power, exponent_or_None] for a nonnegative uint32 value."""


def power_exponent(value):
    if type(value) is not int or not 0 <= value <= 0xffffffff:
        raise ValueError('uint32-range integer required')
    if value == 0 or value & (value - 1):
        return [False, None]
    exponent = 0
    while value > 1:
        value >>= 1
        exponent += 1
    return [True, exponent]
