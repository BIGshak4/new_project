"""In-place binary partition, promised 0/1 values; preserves multiplicities."""


def binary_partition(values):
    left, right = 0, len(values) - 1
    while left <= right:
        if values[left] == 0:
            left += 1
        else:
            values[left], values[right] = values[right], values[left]
            right -= 1
    return values
