"""Exact case-sensitive palindrome over ASCII LETTERS; no normalization/copy.

The edited domain is strings over A..Z/a..z, including the empty string.
Other types/characters raise ValueError rather than being silently filtered.
"""


def is_ascii_palindrome(text):
    if not isinstance(text, str):
        raise ValueError("expected a string of ASCII letters")  # noqa: TRY004 - one rejection type.
    if any(not ("A" <= char <= "Z" or "a" <= char <= "z") for char in text):
        raise ValueError("only ASCII letters A..Z and a..z are accepted")
    left, right = 0, len(text) - 1
    while left < right:
        if text[left] != text[right]:
            return False
        left += 1
        right -= 1
    return True
