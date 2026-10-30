"""Draw a uniform permutation of M*N pixels; zero-based randbelow contract."""

def random_pixels(rows, columns, randbelow):
    if type(rows) is not int or type(columns) is not int or rows < 0 or columns < 0:
        raise ValueError('Dimensions must be nonnegative integers')
    remaining = list(range(rows*columns))
    while remaining:
        j = randbelow(len(remaining)) if len(remaining) > 1 else 0
        if type(j) is not int or not 0 <= j < len(remaining):
            raise ValueError('randbelow(k) must produce 0..k-1')
        chosen = remaining[j]
        remaining[j] = remaining[-1]
        remaining.pop()
        yield divmod(chosen, columns)
