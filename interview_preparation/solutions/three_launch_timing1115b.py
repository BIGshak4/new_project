"""Three sensitizable OR paths use separate signed capture-minus-launch skews."""
from math import isfinite


def budgets(period, capture, setup, hold, paths):
    if len(paths) != 3:
        raise ValueError("exactly three launch paths required")
    common = (period, capture, setup, hold)
    if not all(isfinite(v) for v in common) or period <= 0 or min(setup, hold) < 0:
        raise ValueError("invalid common timing values")
    result = []
    for launch, cq_min, cq_max, logic_min, logic_max in paths:
        values = (launch, cq_min, cq_max, logic_min, logic_max)
        if (not all(isfinite(v) for v in values) or min(cq_min, logic_min) < 0
                or cq_max < cq_min or logic_max < logic_min):
            raise ValueError("invalid path bounds")
        skew = capture - launch
        result.append({"skew": skew,
                       "setup": period + skew - setup - cq_max - logic_max,
                       "hold": cq_min + logic_min - skew - hold})
    return result
