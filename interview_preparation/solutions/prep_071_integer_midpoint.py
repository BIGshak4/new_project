"""Find an integer-midpoint pair in a stream of distinct positive lattice points."""


def first_midpoint_pair(points, dimension):
    if type(dimension) is not int or dimension < 1:
        raise ValueError("dimension must be a positive integer")
    first = {}
    seen = set()
    for values in points:
        point = tuple(values)
        if len(point) != dimension or any(type(v) is not int or v < 1 for v in point):
            raise ValueError(
                "expected a positive integer vector of the declared dimension"
            )
        if point in seen:
            raise ValueError("the stream must contain distinct vectors")
        seen.add(point)
        signature = tuple(value % 2 for value in point)
        if signature in first:
            earlier = first[signature]
            midpoint = tuple((a + b) // 2 for a, b in zip(earlier, point))
            return earlier, point, midpoint
        first[signature] = point
    return None


def guaranteed_draws(dimension):
    if type(dimension) is not int or dimension < 1:
        raise ValueError("dimension must be a positive integer")
    return (1 << dimension) + 1


if __name__ == "__main__":
    print(first_midpoint_pair([(1,), (2,), (5,)], 1))
    print(first_midpoint_pair([(1, 1), (1, 2), (2, 1), (2, 2), (3, 5)], 2))
