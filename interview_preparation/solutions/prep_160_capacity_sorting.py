"""Explicit external-word transfer model and a padded bitonic box example.

The compare/split construction invokes the box five times. No scalar ordering
comparison exists outside the callback. Python's memory list models EXTERNAL
RAM, not extra internal CPU capacity. Each call reads/writes capacity words.
"""


def sorter_only(values, box, *, capacity=1000):
    if type(capacity) is not int or capacity < 2 or capacity % 2:
        raise ValueError("box capacity must be positive, even and at least two")
    if len(values) != 2 * capacity:
        raise ValueError("input needs exactly twice the box capacity")
    memory = list(values)
    block = capacity // 2
    calls = reads = writes = 0
    for left, right in ((0, 1), (2, 3), (0, 2), (1, 3), (1, 2)):
        # These two sorted half-capacity blocks fit the primitive together.
        addresses = list(range(left * block, (left + 1) * block))
        addresses += list(range(right * block, (right + 1) * block))
        loaded = [memory[index] for index in addresses]
        reads += capacity
        ordered = box(loaded)
        calls += 1
        if len(ordered) != capacity:
            raise ValueError("box output must retain its input count")
        for index, value in zip(addresses, ordered, strict=True):
            memory[index] = value
        writes += capacity
    return memory, {"box_calls": calls, "external_reads": reads, "external_writes": writes}


def bitonic_box(values):
    """Ascending numeric sort; padding is a tag, not a guessed numeric infinity."""
    n = len(values)
    padded = 1
    while padded < n:
        padded *= 2
    data = [(0, value) for value in values] + [(1, 0)] * (padded - n)
    comparisons = stages = 0
    span = 2
    while span <= padded:
        distance = span // 2
        while distance:
            stages += 1
            for index in range(padded):
                partner = index ^ distance
                if partner > index:
                    ascending = (index & span) == 0
                    comparisons += 1
                    if (data[index] > data[partner]) == ascending:
                        data[index], data[partner] = data[partner], data[index]
            distance //= 2
        span *= 2
    return [value for padding, value in data[:n]], {"padded_lanes": padded, "comparator_cells": comparisons, "stages": stages}
