"""One finite command string. Final heading is intentionally irrelevant."""
VECTORS = ((0, 1), (1, 0), (0, -1), (-1, 0))


def returns_to_start_with_turnback(commands):
    if not isinstance(commands, str):
        raise ValueError("a command string is required")
    x = y = heading = 0
    for command in commands:
        if command == "R":
            heading = (heading + 1) % 4
        elif command == "L":
            heading = (heading - 1) % 4
        elif command == "T":
            heading = (heading + 2) % 4
        elif command == "M":
            dx, dy = VECTORS[heading]
            x, y = x + dx, y + dy
        else:
            raise ValueError("only uppercase M,R,L,T are allowed")
    return x == 0 and y == 0
