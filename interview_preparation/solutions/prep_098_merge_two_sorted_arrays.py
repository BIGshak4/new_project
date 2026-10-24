"""Merge nondecreasing exact-integer sequences; keep multiplicity, no mutation."""


def merge_sorted(left, right):
    i = j = 0
    output = []
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            output.append(left[i])
            i += 1
        else:
            output.append(right[j])
            j += 1
    while i < len(left):
        output.append(left[i])
        i += 1
    while j < len(right):
        output.append(right[j])
        j += 1
    return output
