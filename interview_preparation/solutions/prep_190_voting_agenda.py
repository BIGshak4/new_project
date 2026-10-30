"""Sincere pairwise voting after tied first-choice and approval totals.

Profiles map strict rankings, e.g. ('A','B','C'), to nonnegative counts.
The source's second ballot is explicitly modelled as two equal approvals.
"""

from collections import Counter
from itertools import permutations

CANDIDATES = ("A", "B", "C")


def tied_profile(x, first_choice_count=37):
    """All profiles with equal first and last counts, parameterized by x."""
    if not isinstance(x, int) or not 0 <= x <= first_choice_count:
        raise ValueError("x must be between zero and the per-candidate total")
    m = first_choice_count
    return dict(zip(permutations(CANDIDATES), (x, m - x, m - x, x, x, m - x)))


def ballot_totals(profile):
    first, approval = Counter(), Counter()
    valid = set(permutations(CANDIDATES))
    for ranking, count in profile.items():
        if ranking not in valid or not isinstance(count, int) or count < 0:
            raise ValueError("Each ballot is a strict ranking with a nonnegative count")
        first[ranking[0]] += count
        for candidate in ranking[:2]:
            approval[candidate] += count
    return dict(first), dict(approval)


def pairwise_votes(profile, first, second):
    if first == second or first not in CANDIDATES or second not in CANDIDATES:
        raise ValueError("Choose two different candidates")
    ballot_totals(profile)
    votes = sum(count for ranking, count in profile.items()
                if ranking.index(first) < ranking.index(second))
    return votes, sum(profile.values()) - votes


def agenda_winner(profile, bye):
    """The other two compete, then their winner competes against bye."""
    if bye not in CANDIDATES:
        raise ValueError("Unknown bye candidate")

    def winner(first, second):
        left, right = pairwise_votes(profile, first, second)
        if left == right:
            raise ValueError("The pairwise tie policy is unspecified")
        return first if left > right else second

    others = [candidate for candidate in CANDIDATES if candidate != bye]
    return winner(bye, winner(*others))
