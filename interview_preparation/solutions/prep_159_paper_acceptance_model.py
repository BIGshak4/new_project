"""Synthetic acceptance decisions, not measurements of an actual paper pack."""
from fractions import Fraction


def interval_decision(measured, uncertainty, target, tolerance):
    """Guard band: pass only if the whole measurement interval conforms."""
    measured, uncertainty = Fraction(measured), Fraction(uncertainty)
    if uncertainty < 0:
        raise ValueError("uncertainty must be nonnegative")
    if target is None or tolerance is None:
        return "needs_requirement"
    target, tolerance = Fraction(target), Fraction(tolerance)
    if tolerance < 0:
        raise ValueError("tolerance must be nonnegative")
    observed = measured - uncertainty, measured + uncertainty
    allowed = target - tolerance, target + tolerance
    if allowed[0] <= observed[0] and observed[1] <= allowed[1]:
        return "pass"
    if observed[1] < allowed[0] or observed[0] > allowed[1]:
        return "fail"
    return "inconclusive"


def sheet_dimensions(width, height, uncertainty, tolerance=None):
    """A4 nominal 210x297 mm; tolerance is supplied, never inferred here."""
    if width <= 0 or height <= 0:
        raise ValueError("positive measured dimensions required")
    short, long = sorted((width, height))
    return {"short_side": interval_decision(short, uncertainty, 210, tolerance),
            "long_side": interval_decision(long, uncertainty, 297, tolerance)}


def count_decision(observed, declared=None):
    if type(observed) is not int or observed < 0:
        raise ValueError("observed count must be a nonnegative integer")
    if declared is None:
        return "needs_requirement"
    if type(declared) is not int or declared < 0:
        raise ValueError("declared count must be a nonnegative integer")
    return "pass" if observed == declared else "fail"
