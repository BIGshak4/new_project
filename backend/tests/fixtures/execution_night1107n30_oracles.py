"""Independent admin expectations, never exposed as learner solution assets."""
import re
from math import comb


def longest_oracle(bits):
    candidates = [(j - i + 1, -i, i, j)
                  for i in range(len(bits)) for j in range(i, len(bits))
                  if all(bits[k] for k in range(i, j + 1))]
    return list(max(candidates)[2:]) if candidates else [-1, -1]


def atoi_stdout_oracle(text):
    match = re.match(r'^[ \t\n\r\f\v]*([+-]?)([0-9]+)', text)
    value = int(match.group(2)) * (-1 if match.group(1) == '-' else 1) if match else 0
    return str(max(-(1 << 31), min((1 << 31) - 1, value))) + '\n'


def boxes_oracle(image):
    parent = {(r, c): (r, c) for r, row in enumerate(image) for c, bit in enumerate(row) if bit}

    def find(pixel):
        while parent[pixel] != pixel:
            pixel = parent[pixel]
        return pixel

    for r, c in parent:
        for other in ((r - 1, c), (r, c - 1)):
            if other in parent:
                parent[find((r, c))] = find(other)
    groups = {}
    for pixel in parent:
        groups.setdefault(find(pixel), []).append(pixel)
    return [[min(r for r, _ in g), min(c for _, c in g), max(r for r, _ in g), max(c for _, c in g)]
            for g in sorted(groups.values(), key=min)]


def grid_oracle(n):
    return comb(2 * n - 2, n - 1)


ORACLES = {
    'prep-longest-ones-interval': longest_oracle,
    'prep-cpp-atoi-style-parser': atoi_stdout_oracle,
    'prep-black-component-bounding-boxes': boxes_oracle,
    'prep-monotone-grid-paths-dp': grid_oracle,
}
