"""Finite epistemic worlds for the explicitly strengthened public-signal puzzle.

The source alone is insufficient. The edited model publicly establishes at
least one liar, compulsory first-opportunity signaling once, simultaneous rounds
and observation of silence. A world bit identifies one husband's liar status.
Women see all bits except their own. Signals are abstract audible events.
"""


def first_signal_layers(population: int, *, common_exists: bool = True):
    """Enumerate small worlds using indistinguishability, not a popcount rule.

    Limit this explanatory model to <=12 couples. The induction, rather than
    enumeration of 2**200 worlds, handles the actual 200-couple question.
    """
    if type(population) is not int or not 1 <= population <= 12:
        raise ValueError("finite model requires 1..12 couples")
    worlds = set(range(1 if common_exists else 0, 1 << population))
    first_events = {}
    for round_number in range(1, population + 1):
        producing_signal = {}
        for world in worlds:
            actors = tuple(
                woman for woman in range(population)
                if world & (1 << woman) and world ^ (1 << woman) not in worlds
            )
            if actors:
                producing_signal[world] = actors
        for world, actors in producing_signal.items():
            first_events[world] = (round_number, actors)
        # Continue only along the publicly observed all-silent branch.
        worlds.difference_update(producing_signal)
    return first_events, worlds


def elapsed_whole_hours(start_hour: int, observed_hour: int, *, days_later: int) -> int:
    """First opportunity is one hour AFTER the announcement, never that same hour."""
    for hour in (start_hour, observed_hour):
        if type(hour) is not int or not 0 <= hour < 24:
            raise ValueError("clock hours must be integers in 0..23")
    if type(days_later) is not int or days_later < 0:
        raise ValueError("days_later must be a nonnegative integer")
    elapsed = 24 * days_later + observed_hour - start_hour
    if elapsed < 1:
        raise ValueError("observation must follow at least the first opportunity")
    return elapsed


def source_only_counterexamples():
    """Permitted histories when the source's missing timing restrictions are absent."""
    return {
        "repeat_allowed": {"liars": 1, "air_signal_rounds": (1, 2, 3, 4, 5)},
        "first_eligible_not_compulsory": {"liars": 1, "air_signal_rounds": (5,)},
        "edited_first_signal": {"liars": 5, "air_signal_rounds": (5,)},
    }
