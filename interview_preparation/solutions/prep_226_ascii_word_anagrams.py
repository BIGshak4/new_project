"""Case-sensitive ASCII A..Z/a..z only; empty strings are valid words."""


def are_anagrams(left, right):
    if any(not ('A' <= ch <= 'Z' or 'a' <= ch <= 'z') for word in (left, right) for ch in word):
        raise ValueError('ASCII letters only')
    if len(left) != len(right):
        return False
    balance = [0] * 128
    for a, b in zip(left, right):
        balance[ord(a)] += 1
        balance[ord(b)] -= 1
    return all(count == 0 for count in balance)
