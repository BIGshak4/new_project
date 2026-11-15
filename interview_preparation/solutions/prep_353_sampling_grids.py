"""Integer pixel coordinates, positive spacings, finite Cartesian grids."""
from math import gcd


def grid_valid(width, height, grid):
    values = [width, height, *grid] if isinstance(grid, (list, tuple)) else []
    if len(values) != 8 or any(type(value) is not int for value in values):
        return False
    x, y, dx, dy, nx, ny = grid
    return (width > 0 and height > 0 and dx > 0 and dy > 0
            and nx > 0 and ny > 0 and x >= 0 and y >= 0
            and x + (nx - 1) * dx < width
            and y + (ny - 1) * dy < height)


def progression_intersects(a, step_a, count_a, b, step_b, count_b):
    """The arguments describe two nonempty finite increasing progressions."""
    low = max(a, b)
    high = min(a + step_a * (count_a - 1), b + step_b * (count_b - 1))
    common = gcd(step_a, step_b)
    if low > high or (b - a) % common:
        return False
    modulus = step_b // common
    index = 0 if modulus == 1 else (
        (b - a) // common * pow(step_a // common, -1, modulus)
    ) % modulus
    first = a + index * step_a
    period = step_a * modulus
    if first < low:
        first += ((low - first + period - 1) // period) * period
    return first <= high


def colored_grids_valid(width, height, green, red):
    if not grid_valid(width, height, green) or not grid_valid(width, height, red):
        return False
    gx, gy, gdx, gdy, gnx, gny = green
    rx, ry, rdx, rdy, rnx, rny = red
    for ox in range(-2, 3):
        for oy in range(-2, 3):
            if not 0 < ox * ox + oy * oy <= 4:
                continue
            if (progression_intersects(gx, gdx, gnx, rx - ox, rdx, rnx)
                    and progression_intersects(gy, gdy, gny, ry - oy, rdy, rny)):
                return False
    return True
