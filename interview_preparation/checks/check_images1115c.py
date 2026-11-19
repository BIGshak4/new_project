"""Independent finite oracles for sampling grids, image levels and drainage."""
import copy
import hashlib
import itertools
import json
import random
import runpy
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRID = runpy.run_path(str(ROOT / "solutions/prep_353_sampling_grids.py"))
PYRAMID = runpy.run_path(str(ROOT / "solutions/prep_354_image_pyramid.py"))
BASINS = runpy.run_path(str(ROOT / "solutions/prep_355_plateau_basins.py"))


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


def main():
    rng = random.Random(1115)
    count = Counter()
    progressions = [(start, step, size) for start in range(-2, 3)
                    for step in range(1, 5) for size in range(1, 5)]
    for left, right in itertools.product(progressions, repeat=2):
        a, d, n = left
        b, e, m = right
        expected = bool(set(a + i * d for i in range(n))
                        & set(b + j * e for j in range(m)))
        assert GRID["progression_intersects"](*left, *right) == expected
        count["progression_pairs"] += 1
    for _ in range(12000):
        width, height = rng.randrange(1, 12), rng.randrange(1, 12)
        green, red = [[rng.randrange(-1, 10), rng.randrange(-1, 10),
                       rng.randrange(0, 6), rng.randrange(0, 6),
                       rng.randrange(0, 5), rng.randrange(0, 5)] for _ in range(2)]
        expected = grid_oracle(width, height, green, red)
        assert GRID["colored_grids_valid"](width, height, green, red) == expected
        count["colored_grid_cases"] += 1
    special_grids = [
        (8, 8, [0, 0, 3, 3, 2, 2], [0, 0, 3, 3, 2, 2]),
        (8, 8, [0, 0, 1, 1, 1, 1], [0, 0, 2, 1, 2, 1]),
        (8, 8, [0, 0, 1, 1, 1, 1], [2, 1, 1, 1, 1, 1]),
        (8, 8, [0, 0, 1, 1, 1, 1], [2, 0, 1, 1, 1, 1]),
    ]
    for case in special_grids:
        assert GRID["colored_grids_valid"](*case) == grid_oracle(*case)
        count["colored_grid_cases"] += 1
    enormous = [0, 0, 10, 10, 10**20, 10**20]
    assert GRID["colored_grids_valid"](10**22, 10**22, enormous, enormous)
    shifted = [3, 0, 10, 10, 10**20, 10**20]
    assert GRID["colored_grids_valid"](10**22, 10**22, enormous, shifted)
    shifted[0] = 2
    assert not GRID["colored_grids_valid"](10**22, 10**22, enormous, shifted)
    count["huge_integer_cases"] = 3
    for rows, columns, levels in itertools.product(range(1, 10), range(1, 10), range(5)):
        image = [[rng.randrange(256) for _ in range(columns)] for _ in range(rows)]
        before = copy.deepcopy(image)
        expected = pyramid_oracle(image, levels)
        assert PYRAMID["image_pyramid"](image, levels) == expected
        assert PYRAMID["collect_stream_pyramid"](iter(image), levels) == expected
        assert image == before
        count["pyramid_cases"] += 1
    assert PYRAMID["image_pyramid"]([[0, 9], [18, 27]], 1) == [[[0, 9], [18, 27]], [[9]]]
    assert PYRAMID["collect_stream_pyramid"]([[7]], 1100) == [[[7]]] * 1101
    mutated = [[] for _ in range(4)]

    def consumer(level, row):
        mutated[level].append(row.copy())
        row[:] = [999] * len(row)
    PYRAMID["stream_pyramid"]([[7] * 3 for _ in range(5)], 3, consumer)
    assert mutated == pyramid_oracle([[7] * 3 for _ in range(5)], 3)
    count["pyramid_boundary_and_ownership_cases"] = 3
    for dimensions, alphabet in [((2, 3), range(3)), ((3, 3), range(2))]:
        rows, columns = dimensions
        for values in itertools.product(alphabet, repeat=rows * columns):
            matrix = [list(values[y * columns:(y + 1) * columns]) for y in range(rows)]
            labels, sizes = basin_oracle(matrix)
            actual_labels, _ = BASINS["drainage_labels"](matrix)
            assert actual_labels == labels
            assert BASINS["basin_sizes"](matrix) == sizes
            count["exhaustive_basin_cases"] += 1
    for _ in range(500):
        rows, columns = rng.randrange(1, 8), rng.randrange(1, 8)
        matrix = [[rng.randrange(-3, 7) for _ in range(columns)] for _ in range(rows)]
        labels, sizes = basin_oracle(matrix)
        assert BASINS["drainage_labels"](matrix)[0] == labels
        assert BASINS["basin_sizes"](matrix) == sizes
        assert sum(sizes) == rows * columns
        count["random_basin_cases"] += 1
    example = [[2, 1, 1], [7, 1, 1], [9, 6, 3]]
    assert BASINS["basin_sizes"](example) == [9]
    assert BASINS["basin_sizes"]([[0, 9, 1]]) == [2, 1]
    count["source_completed_examples"] = 2
    paths = ["solutions/prep_353_sampling_grids.py", "solutions/prep_354_image_pyramid.py",
             "solutions/prep_355_plateau_basins.py", "checks/check_images1115c.py"]
    hashes = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}
    report = dict(result="passed", counts=dict(count), sha256=hashes,
                  scope="Executed Python functions and independent finite combinatorial oracles; no image-processing library or physical water-flow simulation.")
    (ROOT / "checks/images1115c-verification.json").write_text(json.dumps(report, indent=2) + "\n")
    for ident, keys in [(353, ["progression_pairs", "colored_grid_cases", "huge_integer_cases"]),
                        (354, ["pyramid_cases", "pyramid_boundary_and_ownership_cases"]),
                        (355, ["exhaustive_basin_cases", "random_basin_cases", "source_completed_examples"])]:
        (ROOT / f"checks/prep-{ident}-1115c-verification.json").write_text(json.dumps(
            dict(question_id=f"PREP-{ident}", passed=True,
                 counts={key: count[key] for key in keys}), indent=2) + "\n")
    print(json.dumps(dict(count)))


if __name__ == "__main__":
    main()
