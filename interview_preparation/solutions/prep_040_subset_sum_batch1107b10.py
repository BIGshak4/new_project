"""Nonempty subset existence; each index is used at most once, signed ints allowed."""


def has_subset_sum(values, target):
    reachable = set()
    for value in values:
        new_sums = {value}
        for previous in reachable:
            new_sums.add(previous + value)
        reachable.update(new_sums)
        if target in reachable:
            return True
    return False
