"""Exact monotone paths on an n-by-n node grid, no binomial in candidate."""


def grid_paths(n):
    if type(n) is not int or n < 1:
        raise ValueError("n must be a positive integer")
    ways = [1] * n
    for _ in range(1, n):
        for column in range(1, n):
            ways[column] += ways[column - 1]
    return ways[-1]
