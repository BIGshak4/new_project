"""Two adaptive balance queries; no weights or true counterfeit index given."""


def find_lighter(weigh):
    """weigh(left,right): -1 left lighter,0 equal,+1 right lighter."""
    first = weigh((0, 1, 2), (3, 4, 5))
    if type(first) is not int or first not in (-1, 0, 1):
        raise ValueError("invalid balance outcome")
    group = (0, 1, 2) if first == -1 else (3, 4, 5) if first == 1 else (6, 7, 8)
    second = weigh((group[0],), (group[1],))
    if type(second) is not int or second not in (-1, 0, 1):
        raise ValueError("invalid balance outcome")
    return group[0] if second == -1 else group[1] if second == 1 else group[2]
