"""Eight-neighbor plateau drainage with deterministic lower-boundary outlets."""
from collections import Counter


def drainage_labels(heights):
    if (not isinstance(heights, list) or not heights
            or not isinstance(heights[0], list) or not heights[0]):
        raise ValueError("nonempty rectangular integer matrix required")
    rows, columns = len(heights), len(heights[0])
    if any(not isinstance(row, list) or len(row) != columns
           or any(type(value) is not int for value in row) for row in heights):
        raise ValueError("nonempty rectangular integer matrix required")
    size = rows * columns
    parent = list(range(size))
    rank = [0] * size

    def find(cell):
        while parent[cell] != cell:
            parent[cell] = parent[parent[cell]]
            cell = parent[cell]
        return cell

    def unite(a, b):
        a, b = find(a), find(b)
        if a == b:
            return
        if rank[a] < rank[b]:
            a, b = b, a
        parent[b] = a
        if rank[a] == rank[b]:
            rank[a] += 1

    for y in range(rows):
        for x in range(columns):
            for dy, dx in ((-1, -1), (-1, 0), (-1, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if (0 <= yy < rows and 0 <= xx < columns
                        and heights[yy][xx] == heights[y][x]):
                    unite(y * columns + x, yy * columns + xx)
    roots = [find(cell) for cell in range(size)]
    outlets = {}
    for y in range(rows):
        for x in range(columns):
            root = roots[y * columns + x]
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if (0 <= yy < rows and 0 <= xx < columns
                            and heights[yy][xx] < heights[y][x]):
                        candidate = (heights[yy][xx], yy, xx)
                        if root not in outlets or candidate < outlets[root]:
                            outlets[root] = candidate
    flow = {root: roots[y * columns + x]
            for root, (_, y, x) in outlets.items()}
    sinks = {}
    for root in set(roots):
        path = []
        current = root
        while current not in sinks and current in flow:
            path.append(current)
            current = flow[current]
        destination = sinks.get(current, current)
        sinks[current] = destination
        for member in path:
            sinks[member] = destination
    # Label sinks by the first cell of their own plateau in row-major order.
    labels_for_sink = {}
    for cell, root in enumerate(roots):
        if sinks[root] == root and root not in labels_for_sink:
            labels_for_sink[root] = len(labels_for_sink)
    labels = [[labels_for_sink[sinks[roots[y * columns + x]]]
               for x in range(columns)] for y in range(rows)]
    counts = Counter(value for row in labels for value in row)
    sizes = [counts[label] for label in range(len(labels_for_sink))]
    return labels, sizes


def basin_sizes(heights):
    _, sizes = drainage_labels(heights)
    return sorted(sizes, reverse=True)
