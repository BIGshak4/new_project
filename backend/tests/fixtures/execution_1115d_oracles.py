"""Independent finite oracles for the November 15 fourth intake."""
from decimal import Decimal


def scaled_integer_values(strings):
    """Build one decimal integer ruler without Fraction or Decimal arithmetic."""
    parts = [Decimal(s).as_tuple() for s in strings]
    places = max(0, max(-part.exponent for part in parts))
    values = []
    for sign, digits, exponent in parts:
        magnitude = int(''.join(map(str, digits)) or '0')
        values.append((-1 if sign else 1) * magnitude * 10 ** (exponent + places))
    return values, 10 ** places


def voltage_oracle(start, stop, step, failed_voltages):
    from math import gcd
    values, scale = scaled_integer_values([start, stop, step, *failed_voltages])
    a, b, h = values[:3]
    failed = set(values[3:])
    # Independent integer range construction, strictly excluding both bounds.
    failures = [voltage for voltage in range(a + h, b, h) if voltage in failed]
    if not failures:
        return None
    numerator = min(failures)
    divisor = gcd(numerator, scale)
    return [numerator // divisor, scale // divisor]


def different_oracle(a, b):
    # Search the four canonical candidates by bit constraints, not the formula.
    candidates = [value for value in range(4)
                  if value % 2 != a % 2 and (value // 2) % 2 != (b // 2) % 2]
    assert len(candidates) == 1
    return candidates[0]


def distance_oracle(left, right):
    return min((abs(a - b) for a in left for b in right), default=None)


ORACLES = {
    'prep-first-failure-exact-decimal-voltage-grid': voltage_oracle,
    'prep-branch-free-uint32-different-from-two-inputs': different_oracle,
    'prep-minimum-absolute-distance-between-two-arrays': distance_oracle,
}
