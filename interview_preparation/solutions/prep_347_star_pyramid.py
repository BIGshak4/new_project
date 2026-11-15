"""Return a centered pyramid with odd positive base width and no trailing spaces."""


def pyramid(width):
    if type(width) is not int or width <= 0 or width % 2 == 0:
        raise ValueError("base width must be an odd positive integer")
    return "\n".join(" " * ((width - stars) // 2) + "*" * stars
                     for stars in range(1, width + 1, 2))


def pyramid_by_cells(width):
    if type(width) is not int or width <= 0 or width % 2 == 0:
        raise ValueError("base width must be an odd positive integer")
    rows = []
    height = (width + 1) // 2
    for row in range(height):
        cells = []
        for column in range(height + row):
            cells.append(" " if column < height - row - 1 else "*")
        rows.append("".join(cells))
    return "\n".join(rows)
