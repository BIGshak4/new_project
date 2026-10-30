"""Same triangular sum, recursive versus iterative; nonnegative n only."""

def recursive_sum(n):
    if type(n) is not int or n < 0:
        raise ValueError('Nonnegative integer required')
    if n == 0:
        return 0
    return n + recursive_sum(n-1)

def iterative_sum(n):
    if type(n) is not int or n < 0:
        raise ValueError('Nonnegative integer required')
    result = 0
    while n:
        result += n
        n -= 1
    return result
