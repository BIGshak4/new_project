"""Opposite-vertex paths on a cube surface; a is a positive finite side."""

from math import hypot, isfinite, sqrt


def shortest_surface_length(side):
    if not isfinite(side) or side <= 0:
        raise ValueError("The cube side must be positive and finite")
    return side * sqrt(5)


def path_via_shared_edge(side, edge_offset):
    if not isfinite(side) or side <= 0 or not isfinite(edge_offset):
        raise ValueError("Finite side and edge offset required")
    if not 0 <= edge_offset <= side:
        raise ValueError("Crossing point must lie on the common edge")
    return hypot(side, edge_offset) + hypot(side, side - edge_offset)


def unfolded_path(side):
    shortest_surface_length(side)
    return ((0, 0), (side, side / 2), (2 * side, side))
