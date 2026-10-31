"""In-place uppercase ASCII counting sort; input need not contain unique letters."""


def sort_uppercase(letters):
    if any(not isinstance(ch, str) or len(ch) != 1 or not 'A' <= ch <= 'Z' for ch in letters):
        raise ValueError('single uppercase ASCII letters required')
    counts = [0] * 26
    for ch in letters:
        counts[ord(ch) - ord('A')] += 1
    write = 0
    for index, count in enumerate(counts):
        for _ in range(count):
            letters[write] = chr(ord('A') + index)
            write += 1
    return letters


def uppercase_sorted_text(text):
    """Execution adapter; the core operation modifies its character list."""
    return ''.join(sort_uppercase(list(text)))
