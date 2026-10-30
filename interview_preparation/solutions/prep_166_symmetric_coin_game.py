"""Exact rational disk legality and a center/half-turn response strategy."""

from fractions import Fraction


def legal_center(point, placed, table_radius, coin_radius):
    x, y = map(Fraction, point)
    big, small = Fraction(table_radius), Fraction(coin_radius)
    if big <= 0 or small <= 0:
        raise ValueError("positive radii required")
    if small > big or x * x + y * y > (big - small) ** 2:
        return False
    return all((x - a) ** 2 + (y - b) ** 2 >= (2 * small) ** 2 for a, b in placed)


def reflected_response(point):
    return -point[0], -point[1]


def initial_move(table_radius, coin_radius):
    if not legal_center((0, 0), (), table_radius, coin_radius):
        raise ValueError("at least one coin must fit")
    return Fraction(0), Fraction(0)
