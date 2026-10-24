"""Domain promise: x is 9 or 13. No conditionals or validation branches."""


def toggle_nine_thirteen(x):
    return x ^ 4


def toggle_pair(x, first, second):
    """Generalization requires x in {first, second}; not a general replacement."""
    return x ^ first ^ second
