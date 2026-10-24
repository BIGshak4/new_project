"""Exact partitions of an explicitly added ideal 4x4 source reconstruction.

Coordinates: x rightward, y downward, outer square [0,4]^2. Black cells
(1,1), (2,1), (1,2) are excluded. Equal pieces are congruent WITHIN each
region, not between regions. Boundaries have zero area.
"""
from fractions import Fraction as F


def rectangle(x0, y0, x1, y1):
    return [(F(x0), F(y0)), (F(x1), F(y0)),
            (F(x1), F(y1)), (F(x0), F(y1))]


def polygon_area(vertices):
    return abs(F(sum(x * vertices[(i + 1) % len(vertices)][1]
                   - y * vertices[(i + 1) % len(vertices)][0]
                   for i, (x, y) in enumerate(vertices)))) / 2


def cell_boundary(cells):
    """Outline one connected, hole-free triomino of half-unit cells."""
    edges = set()
    for x, y in cells:
        vertices = [(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)]
        for a, b in zip(vertices, vertices[1:] + vertices[:1]):
            if (b, a) in edges:
                edges.remove((b, a))
            else:
                edges.add((a, b))
    start = min(a for a, _ in edges)
    path, current = [], start
    while True:
        path.append((F(current[0], 2), 2 + F(current[1], 2)))
        following = next(b for a, b in edges if a == current)
        current = following
        if current == start:
            break
    return path


C_TILES = [
    [(0, 0), (1, 0), (0, 1)],
    [(1, 1), (1, 2), (2, 2)],
    [(0, 2), (0, 3), (1, 3)],
    [(3, 2), (2, 3), (3, 3)],
]


def region_polygons():
    return {
        "A": [(2, 0), (4, 0), (4, 2), (3, 2), (3, 1), (2, 1)],
        "B": [(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)],
        "C": [(0, 2), (1, 2), (1, 3), (2, 3), (2, 4), (0, 4)],
        "D": rectangle(2, 2, 4, 4),
    }


def partitions():
    return {
        "A": [[(2, 0), (4, 0), (3, 1), (2, 1)],
              [(4, 0), (4, 2), (3, 2), (3, 1)]],
        "B": [rectangle(0, 0, 1, 1), rectangle(1, 0, 2, 1),
              rectangle(0, 1, 1, 2)],
        "C": [cell_boundary(cells) for cells in C_TILES],
        "D": [rectangle(2, 2 + F(2 * i, 7), 4, 2 + F(2 * (i + 1), 7))
              for i in range(7)],
    }
