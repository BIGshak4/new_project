"""Exact vertex median in an undirected positive integer-length street graph."""
from heapq import heappop, heappush


def street_meeting_point(vertex_count, edges, people):
    if type(vertex_count) is not int or vertex_count <= 0:
        raise ValueError('positive vertex count required')
    graph = [[] for _ in range(vertex_count)]
    for u, v, length in edges:
        if (type(u) is not int or type(v) is not int
                or not 0 <= u < vertex_count or not 0 <= v < vertex_count
                or type(length) is not int or length <= 0):
            raise ValueError('valid endpoints and positive integer lengths required')
        graph[u].append((v, length))
        graph[v].append((u, length))
    if (not isinstance(people, list) or not people
            or any(type(p) is not int or not 0 <= p < vertex_count for p in people)):
        raise ValueError('at least one valid person vertex required')
    totals = [0] * vertex_count
    reachable = [True] * vertex_count
    for origin in people:
        distances = [None] * vertex_count
        distances[origin] = 0
        heap = [(0, origin)]
        while heap:
            distance, u = heappop(heap)
            if distances[u] != distance:
                continue
            for v, length in graph[u]:
                candidate = distance + length
                if distances[v] is None or candidate < distances[v]:
                    distances[v] = candidate
                    heappush(heap, (candidate, v))
        for v, distance in enumerate(distances):
            if distance is None:
                reachable[v] = False
            else:
                totals[v] += distance
    candidates = [v for v in range(vertex_count) if reachable[v]]
    if not candidates:
        return None
    best = min(candidates, key=lambda v: (totals[v], v))
    return best, totals[best]


def grid_meeting_point(points):
    """Separate specialization: unobstructed L1 grid, not an arbitrary graph."""
    if not points or any(len(p) != 2 or any(type(x) is not int for x in p) for p in points):
        raise ValueError('nonempty integer coordinate pairs required')
    xs, ys = sorted(p[0] for p in points), sorted(p[1] for p in points)
    x, y = xs[len(xs) // 2], ys[len(ys) // 2]
    return (x, y), sum(abs(a - x) + abs(b - y) for a, b in points)
