"""Exact DC midpoint solution; every resistance is positive and finite."""
from fractions import Fraction as F


def bridge(r1, r2, r3, r4, r5, volts=1):
    r1,r2,r3,r4,r5 = map(F, (r1,r2,r3,r4,r5))
    volts = F(volts)
    if min(r1,r2,r3,r4,r5) <= 0:
        raise ValueError("Positive finite resistances required")
    a = 1/r1 + 1/r2 + 1/r5
    b = -1/r5
    c = 1/r3 + 1/r4 + 1/r5
    u,v = volts/r1, volts/r3
    determinant = a*c-b*b
    left = (u*c-b*v)/determinant
    right = (a*v-b*u)/determinant
    return left, right, (left-right)/r5


def balanced(r1, r2, r3, r4):
    if min(r1,r2,r3,r4) <= 0:
        raise ValueError("Positive finite resistances required")
    return F(r1)*F(r4) == F(r2)*F(r3)
