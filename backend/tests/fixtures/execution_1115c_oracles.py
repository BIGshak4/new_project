import copy
from collections import Counter, deque


def grid_oracle(width, height, green, red):
    def points(grid):
        if (type(width) is not int or type(height) is not int
                or width <= 0 or height <= 0 or not isinstance(grid, list)
                or len(grid) != 6 or any(type(v) is not int for v in grid)):
            return None
        x, y, dx, dy, nx, ny = grid
        if min(dx, dy, nx, ny) <= 0:
            return None
        cells = [(x + i * dx, y + j * dy) for i in range(nx) for j in range(ny)]
        if any(not (0 <= x < width and 0 <= y < height) for x, y in cells):
            return None
        return cells
    left, right = points(green), points(red)
    if left is None or right is None:
        return False
    return all((x - xx) ** 2 + (y - yy) ** 2 == 0
               or (x - xx) ** 2 + (y - yy) ** 2 > 4
               for x, y in left for xx, yy in right)


def pyramid_oracle(image, levels):
    current = copy.deepcopy(image)
    result = [current]
    for _ in range(levels):
        rows, columns = len(current), len(current[0])
        blurred = []
        for y in range(rows):
            row = []
            for x in range(columns):
                samples = [current[min(rows - 1, max(0, y + dy))]
                                  [min(columns - 1, max(0, x + dx))]
                           for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
                row.append(sum(samples) // 9)
            blurred.append(row)
        current = [row[::2] for row in blurred[::2]]
        result.append(current)
    return result


def basin_oracle(matrix):
    rows, columns = len(matrix), len(matrix[0])
    component = {}
    members = []

    def neighbors(y, x):
        for yy in range(max(0, y - 1), min(rows, y + 2)):
            for xx in range(max(0, x - 1), min(columns, x + 2)):
                if (yy, xx) != (y, x):
                    yield yy, xx

    for y in range(rows):
        for x in range(columns):
            if (y, x) in component:
                continue
            index = len(members)
            queue = deque([(y, x)])
            component[y, x] = index
            region = []
            while queue:
                yy, xx = queue.popleft()
                region.append((yy, xx))
                for p in neighbors(yy, xx):
                    if p not in component and matrix[p[0]][p[1]] == matrix[y][x]:
                        component[p] = index
                        queue.append(p)
            members.append(region)
    successor = {}
    for index, region in enumerate(members):
        options = []
        for y, x in region:
            options.extend((matrix[yy][xx], yy, xx) for yy, xx in neighbors(y, x)
                           if matrix[yy][xx] < matrix[y][x])
        if options:
            _, y, x = min(options)
            successor[index] = component[y, x]
    destinations = {}
    for cell, index in component.items():
        while index in successor:
            index = successor[index]
        destinations[cell] = min(members[index])
    anchors = {anchor: i for i, anchor in enumerate(sorted(set(destinations.values())))}
    labels = [[anchors[destinations[y, x]] for x in range(columns)] for y in range(rows)]
    return labels, sorted(Counter(destinations.values()).values(), reverse=True)


def basin_sizes_oracle(matrix):
    return basin_oracle(matrix)[1]


def pair_sum_oracle(values):
    candidates = [values[i] + values[j] for i in range(len(values)) for j in range(i + 1, len(values))]
    return max(candidates) if candidates else None


ORACLES = {
    "prep-finite-colored-sampling-grid-validation": grid_oracle,
    "prep-blur-subsample-pyramid-and-row-streaming": pyramid_oracle,
    "prep-eight-neighbor-plateau-drainage-basins": basin_sizes_oracle,
    "prep-top-two-distinct-and-mode": pair_sum_oracle,
}
