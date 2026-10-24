"""Simple undirected handshake graphs, with hosts 0/1 and fixed partner pairs.

At most one handshake per pair, no self-handshakes and no partner handshakes.
The prince is 0, princess 1; all degrees except the prince's are distinct.
"""

from itertools import combinations


def people_count(guest_couples: int) -> int:
    if type(guest_couples) is not int or guest_couples < 0:
        raise ValueError("guest_couples must be a nonnegative integer")
    return 2 * (guest_couples + 1)


def allowed_pairs(guest_couples: int):
    return tuple((a, b) for a, b in combinations(range(people_count(guest_couples)), 2)
                 if a ^ 1 != b)


def degrees(guest_couples: int, edges):
    count = people_count(guest_couples)
    seen, result = set(), [0] * count
    for edge in edges:
        if len(edge) != 2:
            raise ValueError("each handshake must have two endpoints")
        a, b = edge
        if any(type(person) is not int or not 0 <= person < count for person in (a, b)):
            raise ValueError("invalid person")
        if a == b or a ^ 1 == b:
            raise ValueError("self or partner handshake")
        pair = tuple(sorted((a, b)))
        if pair in seen:
            raise ValueError("repeated handshake pair")
        seen.add(pair)
        result[a] += 1
        result[b] += 1
    return tuple(result)


def satisfies_distinctness(guest_couples: int, edges):
    counts = degrees(guest_couples, edges)
    return len(set(counts[1:])) == len(counts) - 1


def construct_example(guest_couples: int):
    """One valid family, for checking feasibility rather than proving necessity."""
    count = people_count(guest_couples)
    target = [guest_couples, guest_couples]
    for low in range(guest_couples):
        target.extend((low, 2 * guest_couples - low))
    edges = tuple((a, b) for a, b in combinations(range(count), 2)
                  if target[a] + target[b] > 2 * guest_couples)
    return edges


def complement_pairs(guest_couples: int):
    """Degree pairs peeled in the proof; the princess keeps the middle degree."""
    people_count(guest_couples)
    return tuple((low, 2 * guest_couples - low) for low in range(guest_couples))
