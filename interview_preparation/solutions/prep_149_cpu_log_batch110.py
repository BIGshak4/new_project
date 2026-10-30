"""Snapshot query for weighted half-open intervals. Requery after new records."""
from fractions import Fraction


def maximum_cpu_usage(records):
    events = {}
    for start, end, usage in records:
        usage = Fraction(usage)
        if not start < end or usage < 0:
            raise ValueError('Require start<end and nonnegative usage')
        events[start] = events.get(start, Fraction(0)) + usage
        events[end] = events.get(end, Fraction(0)) - usage
    current = best = Fraction(0)
    first_time = None
    for time in sorted(events):
        current += events[time]
        if current > best:
            best, first_time = current, time
    return best, first_time
