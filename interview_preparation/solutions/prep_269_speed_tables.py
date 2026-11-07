"""Branch-free core for promised integer speed in [0,10]."""
GAS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10)
BRAKE = (0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9)


def gas(speed):
    return GAS[speed]


def brake(speed):
    return BRAKE[speed]


def speed_controls(speed):
    """Runtime adapter: return [gas(speed), brake(speed)] for one promised speed."""
    return [gas(speed), brake(speed)]
