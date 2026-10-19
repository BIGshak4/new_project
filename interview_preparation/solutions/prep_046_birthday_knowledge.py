"""Public-announcement reasoning for Dani's birthday; dates are (month, day)."""
from collections import Counter
from collections.abc import Iterable

DATES = ((5, 15), (5, 16), (5, 19), (6, 17), (6, 18),
         (7, 14), (7, 16), (8, 14), (8, 15), (8, 17))


def birthday_stages(candidates: Iterable[tuple[int, int]] = DATES):
    """Return candidates after each truthful public statement.

    Chaim knows the month and Yoni knows the day. They and an observer know
    the initial candidate set and the information assignment. All reasoning
    and truthful public statements are common knowledge. Dates must be unique.
    """
    initial = tuple(sorted(candidates))
    if len(initial) != len(set(initial)):
        raise ValueError("Candidate dates must be distinct")
    initial_day_counts = Counter(day for _, day in initial)
    initial_month_counts = Counter(month for month, _ in initial)
    possible_months = {
        month for month, _ in initial
        if initial_month_counts[month] > 1
        and all(initial_day_counts[day] > 1
                for other_month, day in initial if other_month == month)
    }
    after_chaim = tuple(date for date in initial if date[0] in possible_months)
    current_day_counts = Counter(day for _, day in after_chaim)
    after_yoni = tuple(date for date in after_chaim
                      if initial_day_counts[date[1]] > 1
                      and current_day_counts[date[1]] == 1)
    current_month_counts = Counter(month for month, _ in after_yoni)
    after_final_chaim = tuple(date for date in after_yoni
                              if current_month_counts[date[0]] == 1)
    return {
        "initial": initial,
        "after_chaim": after_chaim,
        "after_yoni": after_yoni,
        "after_final_chaim": after_final_chaim,
    }


if __name__ == "__main__":
    for statement, dates in birthday_stages().items():
        print(statement, [f"{day:02}/{month:02}" for month, day in dates])
