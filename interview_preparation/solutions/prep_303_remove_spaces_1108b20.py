"""Remove literal U+0020 spaces; retain all other code points."""


def remove_spaces(text):
    if not isinstance(text, str):
        raise TypeError("a string is required")
    return "".join(character for character in text if character != " ")
