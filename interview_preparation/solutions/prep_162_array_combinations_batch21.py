"""Two explicitly different interpretations of the source word combinations.

Permutations use every item and deduplicate equal values; values must be hashable.
Subsets choose positions, preserve source order, and may duplicate value-tuples.
"""

from collections import Counter


def distinct_array_permutations(items):
    counts = Counter(items)
    keys, size, path = tuple(counts), sum(counts.values()), []

    def visit():
        if len(path) == size:
            yield tuple(path)
            return
        for value in keys:
            if counts[value]:
                counts[value] -= 1
                path.append(value)
                yield from visit()
                path.pop()
                counts[value] += 1

    yield from visit()


def positional_subsets(items):
    values, chosen = tuple(items), []

    def visit(index):
        if index == len(values):
            yield tuple(chosen)
            return
        yield from visit(index + 1)
        chosen.append(values[index])
        yield from visit(index + 1)
        chosen.pop()

    yield from visit(0)


def print_array_permutations(items):
    for ordering in distinct_array_permutations(items):
        print(list(ordering))
