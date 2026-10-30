"""Same-clock, same-edge, one-cycle path budgets in one consistent time unit."""

from math import isfinite


def timing_slacks(
    period, cq_min, cq_max, logic_min, logic_max, setup, hold, skew=0, setup_uncertainty=0, hold_uncertainty=0
):
    values = (
        period,
        cq_min,
        cq_max,
        logic_min,
        logic_max,
        setup,
        hold,
        skew,
        setup_uncertainty,
        hold_uncertainty,
    )
    if not all(isfinite(value) for value in values):
        raise ValueError("finite timing values required")
    if (
        period <= 0
        or min(cq_min, logic_min, setup, hold, setup_uncertainty, hold_uncertainty) < 0
        or cq_max < cq_min
        or logic_max < logic_min
    ):
        raise ValueError("invalid timing contract")
    # Positive skew means that the capture clock arrives LATER.
    setup_slack = period + skew - setup_uncertainty - setup - cq_max - logic_max
    hold_slack = cq_min + logic_min - skew - hold_uncertainty - hold
    return setup_slack, hold_slack
