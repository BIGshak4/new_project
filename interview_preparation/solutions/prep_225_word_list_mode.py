"""Exact, case-sensitive words; frequency ties prefer first appearance."""


def most_frequent_word(words):
    if not words:
        return None
    counts = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    best = words[0]
    for word in words:
        if counts[word] > counts[best]:
            best = word
    return [best, counts[best]]
