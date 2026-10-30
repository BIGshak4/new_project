"""Seven five-way ordering queries; all ordering is inside the supplied block.

Inputs are 25 distinct hashable values from a total order. Equality/hash lookup
only routes groups. A reusable block needs storage/control; an unrolled network
uses seven block instances plus identity-based conditional routing.
"""


def top_three(values, sorter):
    if len(values) != 25 or len(set(values)) != 25:
        raise ValueError('Expected 25 distinct values')
    groups = [sorter(values[start:start + 5]) for start in range(0, 25, 5)]
    by_winner = {group[0]: group for group in groups}
    winners = sorter([group[0] for group in groups])
    a, b, c = (by_winner[winner] for winner in winners[:3])
    finalists = sorter([a[1], a[2], b[0], b[1], c[0]])
    return [a[0], finalists[0], finalists[1]]
