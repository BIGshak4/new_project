"""In-place ascending comparison sort; integer inputs promised, not stable."""


def sort_array(values):
    def sift_down(root, end):
        while 2 * root + 1 < end:
            child = 2 * root + 1
            if child + 1 < end and values[child + 1] > values[child]:
                child += 1
            if values[root] >= values[child]:
                break
            values[root], values[child] = values[child], values[root]
            root = child

    n = len(values)
    for root in range(n // 2 - 1, -1, -1):
        sift_down(root, n)
    for end in range(n - 1, 0, -1):
        values[0], values[end] = values[end], values[0]
        sift_down(0, end)
    return values
