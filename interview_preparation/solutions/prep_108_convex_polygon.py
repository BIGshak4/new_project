"""Exact convexity for ordered polygon vertices; distinguish the simple promise.

Coordinates are exact integer pairs. The O(n) function requires a simple
boundary with distinct vertices and no repeated closing vertex. The checked
wrapper validates simplicity in O(n^2); neither function sorts the vertices.
"""


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])


def is_convex_simple_polygon(vertices, *, strict=False):
    """O(n) time/O(1) words, conditional on a simple ordered boundary."""
    if len(vertices) < 3:
        return False
    direction = 0
    for index in range(len(vertices)):
        turn = cross(vertices[index - 1], vertices[index], vertices[(index + 1) % len(vertices)])
        if turn == 0:
            if strict:
                return False
        elif direction == 0:
            direction = 1 if turn > 0 else -1
        elif (turn > 0) != (direction > 0):
            return False
    return direction != 0


def on_segment(a, b, point):
    return (cross(a, b, point) == 0
            and min(a[0], b[0]) <= point[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= point[1] <= max(a[1], b[1]))


def segments_intersect(a, b, c, d):
    turns = cross(a, b, c), cross(a, b, d), cross(c, d, a), cross(c, d, b)
    if (turns[0] > 0 > turns[1] or turns[1] > 0 > turns[0]) and (
            turns[2] > 0 > turns[3] or turns[3] > 0 > turns[2]):
        return True
    return ((turns[0] == 0 and on_segment(a, b, c))
            or (turns[1] == 0 and on_segment(a, b, d))
            or (turns[2] == 0 and on_segment(c, d, a))
            or (turns[3] == 0 and on_segment(c, d, b)))


def is_simple_polygon(vertices):
    """Reject repeated vertices, crossings, touches and backtracking overlaps."""
    count = len(vertices)
    if count < 3:
        return False
    for i in range(count):
        for j in range(i + 1, count):
            if vertices[i] == vertices[j]:
                return False
        previous, current, following = vertices[i - 1], vertices[i], vertices[(i + 1) % count]
        if cross(previous, current, following) == 0:
            overlap = ((previous[0] - current[0]) * (following[0] - current[0])
                       + (previous[1] - current[1]) * (following[1] - current[1]))
            if overlap > 0:
                return False
        for j in range(i + 1, count):
            if j == i + 1 or (i == 0 and j == count - 1):
                continue
            if segments_intersect(vertices[i], vertices[(i + 1) % count],
                                  vertices[j], vertices[(j + 1) % count]):
                return False
    return True


def is_convex_polygon(vertices, *, strict=False):
    """Checked O(n^2) wrapper when simple boundary is not already promised."""
    return is_simple_polygon(vertices) and is_convex_simple_polygon(vertices, strict=strict)
