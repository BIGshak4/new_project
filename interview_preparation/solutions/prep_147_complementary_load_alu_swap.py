"""Three controlled capture edges, no spare register and only XOR selected."""


def capture(x, y, load, width):
    """LOAD=1 captures into Y; LOAD=0 captures into X. Other register holds."""
    if type(width) is not int or width < 1:
        raise ValueError("width must be positive")
    if load not in (0, 1) or not (0 <= x < 1 << width and 0 <= y < 1 << width):
        raise ValueError("Invalid fixed-width state or LOAD")
    alu = x ^ y
    return (x, alu) if load else (alu, y)


def swap_trace(x, y, width):
    states = [(x, y)]
    for load in (0, 1, 0):
        x, y = capture(x, y, load, width)
        states.append((x, y))
    return states
