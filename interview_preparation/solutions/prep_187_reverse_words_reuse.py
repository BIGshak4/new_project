"""Reverse words by reusing exactly the character-range reversal operation."""


def reverse_range(chars, left, right):
    """In-place inclusive interval; the empty interval right=left-1 is valid."""
    if not (0 <= left <= len(chars) and left - 1 <= right < len(chars)):
        raise ValueError("Invalid inclusive interval")
    while left < right:
        chars[left], chars[right] = chars[right], chars[left]
        left, right = left + 1, right - 1


def reverse_words_inplace(chars):
    """Words are non-space runs; every ASCII space character is retained."""
    reverse_range(chars, 0, len(chars) - 1)
    start = 0
    for end in range(len(chars) + 1):
        if end == len(chars) or chars[end] == " ":
            reverse_range(chars, start, end - 1)
            start = end + 1


def reverse_words(text):
    chars = list(text)
    reverse_words_inplace(chars)
    return "".join(chars)
