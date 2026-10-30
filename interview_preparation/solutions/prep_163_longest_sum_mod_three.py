"""Longest nonempty contiguous interval with sum divisible by three.

Return (length,start,end), inclusive zero-based bounds. No interval gives
(0,None,None). Equal lengths prefer earliest start, then earliest end.
Source contract is positive integers; an explicit optional extension accepts
all integers with positive_only=False. No full prefix sums are stored.
"""


def longest_mod_three(values, *, positive_only=True):
    earliest = [-1, None, None]
    residue = 0
    best = (0, None, None)
    for end, value in enumerate(values):
        if type(value) is not int or (positive_only and value <= 0):
            raise ValueError("source contract requires positive integers")
        residue = (residue + value) % 3
        if earliest[residue] is None:
            earliest[residue] = end
        else:
            start = earliest[residue] + 1
            length = end - earliest[residue]
            if length > best[0] or (length == best[0] and start < best[1]):
                best = length, start, end
    return best
