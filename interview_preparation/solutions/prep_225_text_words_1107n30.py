"""Whitespace-token text variant; the older list-returning API is unchanged."""


def most_frequent_text_word(text):
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    words = text.split()
    if not words:
        return None
    counts = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    best = words[0]
    for word in words:
        if counts[word] > counts[best]:
            best = word
    return best
