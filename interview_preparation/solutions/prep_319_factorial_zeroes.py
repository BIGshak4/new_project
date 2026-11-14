def trailing_zeroes(n):
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a nonnegative integer")
    zeros = 0
    while n >= 5:
        n //= 5
        zeros += n
    return zeros
