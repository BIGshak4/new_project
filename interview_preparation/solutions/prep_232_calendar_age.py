"""Completed calendar ages and the December/January birthday puzzle.

For an exact date-of-birth model, age increments on the birthday. The finite
search below uses ordinary month/day birthdays (no February 29 convention is
needed for the puzzle's unique December 31 solution).
"""
from datetime import date, timedelta


def age_on(born: date, observed: date) -> int:
    if observed < born:
        raise ValueError("observation precedes birth")
    return observed.year - born.year - ((observed.month, observed.day) < (born.month, born.day))


def age_timeline(year: int) -> dict:
    if type(year) is not int or not 11 <= year <= 9998:
        raise ValueError("year must be in 11..9998")
    born = date(year - 10, 12, 31)
    today = date(year, 1, 1)
    points = {
        "two_days_ago": today - timedelta(days=2),
        "yesterday": today - timedelta(days=1),
        "today": today,
        "birthday_this_year": date(year, 12, 31),
        "birthday_next_year": date(year + 1, 12, 31),
    }
    return {name: {"date": value.isoformat(), "age": age_on(born, value)} for name, value in points.items()}


def find_dates_in_year(year: int) -> list[dict]:
    """Exhaust one supplied calendar year and 365 ordinary birthday dates.

Turning eleven during the following year fixes birth year to year-10. Search
does not assert an exhaustion over all possible years or birthday conventions.
"""
    if type(year) is not int or not 11 <= year <= 9998:
        raise ValueError("year must be in 11..9998")
    ordinary_start = date(2001, 1, 1)
    birthdays = [ordinary_start + timedelta(days=i) for i in range(365)]
    end = date(year + 1, 1, 1)
    today = date(year, 1, 1)
    answers = []
    while today < end:
        ago = today - timedelta(days=2)
        for birthday in birthdays:
            born = date(year - 10, birthday.month, birthday.day)
            if age_on(born, ago) == 8:
                answers.append({"today": today.isoformat(), "birthday": birthday.strftime("%m-%d")})
        today += timedelta(days=1)
    return answers
