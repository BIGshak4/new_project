"""Independent finite checks for two new logic records and two variants.

Counts describe exactly the supplied finite domains, not biological experiments,
all possible calendars, human review or runtime evaluation of learner answers.
"""
from __future__ import annotations

import importlib.util
import json
from datetime import date, timedelta
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / "solutions" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_lions():
    model = load("prep_231_rational_lions_cow")
    examined = set()

    @lru_cache(None)
    def identity_oracle(remaining):
        if not remaining:
            return False
        willing = []
        for lion in remaining:
            others = tuple(x for x in remaining if x != lion)
            survives_eating = not identity_oracle(others)
            eat_utility = (int(survives_eating), 1)
            grass_utility = (1, 0)
            willing.append(eat_utility > grass_utility)
            examined.add((remaining, lion))
        assert len(set(willing)) == 1  # Identity does not change this preference.
        return any(willing)

    for count in range(9):
        assert model.cow_is_eaten(count) == identity_oracle(tuple(range(count)))
    for count in range(501):
        assert model.cow_is_eaten(count) == (count % 2 == 1)
        assert model.cow_is_eaten_constant_space_formula(count) == model.cow_is_eaten(count)
    assert model.outcome(100) == {"lions": 100, "initial_cow_eaten": False, "first_eater_survives": None}
    assert model.outcome(101)["first_eater_survives"] is True
    # If meat outranks survival, even an unsafe eater prefers (meat=1,alive=0)
    # to grass (meat=0,alive=1). With two such lions the initial cow is eaten.
    assert (1, 0) > (0, 1)
    return {"status": "pass", "identity_game_counts": list(range(9)),
            "identity_decisions_checked": len(examined), "parity_counts_checked": 501,
            "hundred_lion_initial_cow_eaten": False, "alternative_preference_counterexample": 2,
            "scope": "Finite deterministic sequential preference model; no biological observation."}


def check_calendar():
    model = load("prep_232_calendar_age")
    years = [2023, 2024, 2025]
    searched_pairs = 0
    for year in years:
        expected = []
        today, end = date(year, 1, 1), date(year + 1, 1, 1)
        birthday_start = date(2001, 1, 1)
        while today < end:
            ago = today - timedelta(days=2)
            for offset in range(365):
                birthday = birthday_start + timedelta(days=offset)
                # Independent event counting: from age eight, reaching eleven
                # next year requires three birthday events strictly after ago.
                events = [date(y, birthday.month, birthday.day) for y in range(ago.year, year + 2)]
                later = [event for event in events if ago < event <= date(year + 1, 12, 31)]
                if len(later) == 3:
                    expected.append({"today": today.isoformat(), "birthday": birthday.strftime("%m-%d")})
                searched_pairs += 1
            today += timedelta(days=1)
        assert model.find_dates_in_year(year) == expected == [{"today": f"{year}-01-01", "birthday": "12-31"}]
        timeline = model.age_timeline(year)
        assert [p["age"] for p in timeline.values()] == [8, 9, 9, 10, 11]
    boundary_cases = [
        (date(2010, 1, 31), date(2024, 1, 30), 13),
        (date(2010, 1, 31), date(2024, 1, 31), 14),
        (date(2010, 2, 28), date(2024, 2, 27), 13),
        (date(2010, 2, 28), date(2024, 2, 28), 14),
        (date(2010, 3, 1), date(2024, 2, 29), 13),
        (date(2010, 3, 1), date(2024, 3, 1), 14),
        (date(2010, 12, 31), date(2024, 1, 1), 13),
        (date(2010, 12, 31), date(2024, 12, 31), 14),
    ]
    for born, observed, expected in boundary_cases:
        assert model.age_on(born, observed) == expected
    return {"status": "pass", "calendar_years_enumerated": years,
            "ordinary_birthday_dates_per_year": 365, "date_birthday_pairs_checked": searched_pairs,
            "boundary_cases": len(boundary_cases), "solution_month_day": "01-01",
            "birthday_month_day": "12-31", "timeline_ages": [8, 9, 9, 10, 11],
            "scope": "Finite dates in the three listed years, with ordinary non-February-29 birthdays; no unbounded-year claim."}


def threshold_dp(maximum):
    """Minimax over first physical drop locations, not triangular capacity."""
    table = [[0] * (maximum + 1) for _ in range(3)]
    for floors in range(1, maximum + 1):
        table[1][floors] = floors
        table[2][floors] = min(1 + max(table[1][drop - 1], table[2][floors - drop])
                               for drop in range(1, floors + 1))
    return table[2]


def check_eggs():
    model = load("prep_025_highest_safe_floor_batch22")
    maximum, scenarios = 100, 0
    dp = threshold_dp(maximum)
    for floors in range(maximum + 1):
        for known in ([False, True] if floors else [False]):
            worst = 0
            for first_break in range(1, floors + 1 + int(not known)):
                trace = []
                result = model.highest_safe_floor(floors, lambda f, threshold=first_break: f >= threshold,
                                                  top_known_breaking=known, trace=trace)
                assert result == first_break - 1
                assert all(1 <= floor <= floors for _, floor, _ in trace)
                if known:
                    assert all(floor < floors for _, floor, _ in trace)
                broken = set()
                for egg, _, did_break in trace:
                    assert egg not in broken
                    if did_break:
                        broken.add(egg)
                assert len(broken) <= 2
                worst = max(worst, len(trace))
                scenarios += 1
            assert worst == model.minimum_drops(floors, top_known_breaking=known) == dp[floors-int(known)]
    assert model.minimum_drops(2) == 2 and model.minimum_drops(2, top_known_breaking=True) == 1
    assert model.minimum_drops(100) == 14
    huge = 10**100
    k = model.minimum_drops(huge)
    assert k*(k+1)//2 >= huge and (k-1)*k//2 < huge
    return {"status": "pass", "floors_exhausted": [0, maximum], "threshold_scenarios": scenarios,
            "contracts": ["no-breaking-floor allowed", "top floor known breaking"],
            "independent_oracle": "Minimax DP over every first test location",
            "hundred_floors_worst_case": 14, "large_exact_integer_case_digits": 101,
            "scope": "Logical stable monotone two-egg oracle; no physical dropping experiment."}


def check_clock():
    model = load("prep_017_general_clock_batch22")
    for total_minutes in range(720):
        hour, minute = divmod(total_minutes, 60)
        phase = (Fraction(11, 2) * total_minutes) % 360
        relative_oracle = min(phase, 360-phase)
        assert model.minor_angle(hour, minute) == relative_oracle
        assert model.minor_angle(hour + 12, minute) == relative_oracle
        assert 0 <= relative_oracle <= 180
    assert model.minor_angle(6, 30) == 15
    assert model.minor_angle(6, 0) == 180
    assert model.minor_angle(0, 0) == model.minor_angle(12, 0) == 0
    assert model.minor_angle(10, 10) == 115
    return {"status": "pass", "distinct_minutes_exhausted": 720, "periodicity_comparisons": 720,
            "six_thirty_degrees": 15, "six_zero_degrees": 180,
            "ten_ten_degrees": 115, "zero_angle_examples": ["00:00", "12:00"],
            "scope": "Exact rational arithmetic, continuous hour hand, integer minute inputs; no clock photograph measurement."}


def check_all():
    return {"PREP-231": check_lions(), "PREP-232": check_calendar(),
            "PREP-025": check_eggs(), "PREP-017": check_clock()}


if __name__ == "__main__":
    reports = check_all()
    for ident, report in reports.items():
        suffix = ident.lower() + ("-batch22" if ident in {"PREP-025", "PREP-017"} else "")
        (BANK / "checks" / f"{suffix}-verification.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(reports, ensure_ascii=False, indent=2))
