"""Single-pass turtle position; final orientation is intentionally ignored."""

VECTORS = ((1, 0), (0, -1), (-1, 0), (0, 1))


def turtle_state(commands):
    x = y = heading = 0
    for command in commands:
        if command == "R":
            heading = (heading + 1) % 4
        elif command == "L":
            heading = (heading - 1) % 4
        elif command == "M":
            dx, dy = VECTORS[heading]
            x, y = x + dx, y + dy
        else:
            raise ValueError("Only uppercase R, L and M are permitted")
    return x, y, heading


def returns_to_start(commands):
    x, y, _ = turtle_state(commands)
    return x == 0 and y == 0
