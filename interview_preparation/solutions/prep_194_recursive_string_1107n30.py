"""A string variant of the completed ADT; flat string operations copy."""


def Head(text):
    return text[0]  # One-character string, not an unwrapped scalar character.


def Tail(text):
    return text[1:]


def Concat(left, right):
    return left + right


def Length(text):
    return len(text)


def reverse_string(text):
    if Length(text) == 0:
        return ""
    return Concat(reverse_string(Tail(text)), Head(text))
