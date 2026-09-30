"""Exactly one digit has odd frequency; all others have even frequency."""


def odd_digit(values):
    """O(n) time, O(1) extra space; caller guarantees digits and parity premise."""
    result = 0
    for value in values:
        result ^= value
    return result


def odd_digit_checked(values):
    """Ten counters validate the premise, retaining O(n) time / O(1) space."""
    counts = [0] * 10
    for value in values:
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
            raise ValueError('Every element must be a digit from 0 through 9')
        counts[value] += 1
    candidates = [digit for digit, count in enumerate(counts) if count % 2]
    if len(candidates) != 1:
        raise ValueError('Exactly one digit must have odd frequency')
    return candidates[0]
