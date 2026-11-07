"""Return A1 grouped by unique A2 priorities, then ascending leftovers."""


def relative_sort(a1, a2):
    if (type(a1) is not list or type(a2) is not list
            or any(type(x) is not int for x in a1)
            or any(type(x) is not int for x in a2)):
        raise ValueError("integer lists required")
    if len(set(a2)) != len(a2):
        raise ValueError("a2 priorities must be unique")
    counts = {}
    for value in a1:
        counts[value] = counts.get(value, 0) + 1
    result = []
    for value in a2:
        for _ in range(counts.pop(value, 0)):
            result.append(value)
    for value in sorted(counts):
        for _ in range(counts[value]):
            result.append(value)
    return result
