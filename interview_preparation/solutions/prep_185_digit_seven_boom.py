"""A boom once per positive integer containing decimal digit 7."""


def contains_seven(number):
    if type(number) is not int or number < 0:
        raise ValueError("A nonnegative integer is required")
    while number:
        if number % 10 == 7:
            return True
        number //= 10
    return False


def seven_flags(limit):
    """Increment decimal digits; membership work is amortized O(1) per number."""
    if type(limit) is not int or limit < 0:
        raise ValueError("A nonnegative integer limit is required")
    digits = [0]  # Least-significant decimal digit first.
    sevens = 0
    for number in range(1, limit + 1):
        place = 0
        while place < len(digits) and digits[place] == 9:
            digits[place] = 0
            place += 1
        if place == len(digits):
            digits.append(1)
        else:
            sevens -= digits[place] == 7
            digits[place] += 1
            sevens += digits[place] == 7
        yield number, sevens > 0


def seven_boom(limit):
    """Emit boom only for matching integers; nonmatching integers emit nothing."""
    for _, boom in seven_flags(limit):
        if boom:
            yield "boom"
