from random import randrange


def median(values):
    """Find the sample median of signed 32-bit integers. May reorder values."""
    n = len(values)
    if not n:
        return None
    middle = n // 2
    lo, hi = 0, n
    while True:
        pivot = values[randrange(lo, hi)]
        left = scan = lo
        right = hi
        while scan < right:
            if values[scan] < pivot:
                values[left], values[scan] = values[scan], values[left]
                left += 1
                scan += 1
            elif values[scan] > pivot:
                right -= 1
                values[scan], values[right] = values[right], values[scan]
            else:
                scan += 1
        if middle < left:
            hi = left
        elif middle >= right:
            lo = right
        else:
            break

    if n % 2:
        return pivot
    lower = max(values[i] for i in range(middle))
    return (lower + pivot) / 2
