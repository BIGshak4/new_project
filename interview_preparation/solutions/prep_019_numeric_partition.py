"""In-place three-way partition of promised exact integers 0,1,2.

One shrinking unclassified interval; positions may be read again after a swap.
No input-wide prevalidation pass, auxiliary array or stability guarantee.
An invalid value raises when reached; earlier mutations need not roll back.
"""


def partition_012(values):
    low = mid = 0
    high = len(values) - 1
    while mid <= high:
        value = values[mid]
        if type(value) is not int:
            raise ValueError("expected exact integers 0,1,2")
        if value == 0:
            values[low], values[mid] = values[mid], values[low]
            low += 1
            mid += 1
        elif value == 1:
            mid += 1
        elif value == 2:
            values[mid], values[high] = values[high], values[mid]
            high -= 1
        else:
            raise ValueError("expected exact integers 0,1,2")
