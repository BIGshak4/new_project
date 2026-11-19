"""Return minimum cross-array absolute distance without changing the inputs."""


def minimum_cross_distance(left, right):
    if not left or not right:
        return None
    a, b = sorted(left), sorted(right)
    i = j = 0
    best = abs(a[0] - b[0])
    while i < len(a) and j < len(b):
        gap = abs(a[i] - b[j])
        best = min(best, gap)
        if gap == 0:
            return 0
        if a[i] < b[j]:
            i += 1
        else:
            j += 1
    return best
