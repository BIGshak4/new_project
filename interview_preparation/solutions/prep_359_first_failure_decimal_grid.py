"""First failing point on an exact, strictly interior decimal-voltage grid."""
from decimal import Decimal, InvalidOperation
from fractions import Fraction


def decimal_fraction(text):
    if not isinstance(text, str):
        raise ValueError("finite decimal strings required")
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("finite decimal strings required") from exc
    if not value.is_finite():
        raise ValueError("finite decimal strings required")
    return Fraction(value)


def find_failure(start, stop, step, test):
    """test(Fraction) is True for pass and False for fail; return Fraction/None."""
    first, limit, increment = map(decimal_fraction, (start, stop, step))
    if first >= limit or increment <= 0:
        raise ValueError("start < stop and positive step required")
    index = 1
    while (voltage := first + index * increment) < limit:
        if not test(voltage):
            return voltage
        index += 1
    return None


def first_failure_voltage(start, stop, step, failed_voltages):
    """JSON exercise adapter: only listed voltages fail, without monotonicity."""
    failures = {decimal_fraction(v) for v in failed_voltages}
    result = find_failure(start, stop, step, lambda voltage: voltage not in failures)
    if result is None:
        return None
    return [result.numerator, result.denominator]
