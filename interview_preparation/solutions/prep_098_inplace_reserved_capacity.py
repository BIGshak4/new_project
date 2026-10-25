"""Merge a into b's valid sorted prefix; b has exactly len(a) reserved slots.

Integer sortedness is promised. Real zeros/negatives/duplicates are valid;
padding contents are ignored. Arrays do not overlap. a remains unchanged.
"""


def merge_into_right(a, b, m):
    if type(m) is not int or m < 0 or len(b) != m + len(a) or a is b:
        raise ValueError("require distinct arrays, valid prefix m and exact capacity m+len(a)")
    i, j, write = len(a) - 1, m - 1, len(b) - 1
    while i >= 0:
        if j >= 0 and b[j] >= a[i]:
            b[write] = b[j]
            j -= 1
        else:
            b[write] = a[i]
            i -= 1
        write -= 1
    return b
