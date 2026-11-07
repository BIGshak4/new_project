"""n sorted distinct observations from 1..n+1; exactly one missing (promised)."""


def sorted_missing(values):
    low, high = 0, len(values)
    while low < high:
        middle = low + (high - low) // 2
        if values[middle] == middle + 1:
            low = middle + 1
        else:
            high = middle
    return low + 1
