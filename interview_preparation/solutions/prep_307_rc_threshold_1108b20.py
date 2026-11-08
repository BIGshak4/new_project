"""Single threshold at TWO thirds in both source clauses; no hysteresis."""
import math
from fractions import Fraction as F


def divider(vs, top_r, bottom_r):
    vs, top_r, bottom_r = map(F, (vs, top_r, bottom_r))
    if vs <= 0 or min(top_r,bottom_r) <= 0:
        raise ValueError('Positive source and resistances required')
    return vs*bottom_r/(top_r+bottom_r)


def capacitor_voltage(vs, tau, time, initial=0):
    if vs <= 0 or tau <= 0 or time < 0:
        raise ValueError('Require Vs>0, tau>0, time>=0')
    return vs+(initial-vs)*math.exp(-time/tau)


def comparator(vcap, reference):
    return int(vcap > reference)  # Ideal source contract: equality returns zero.


def charging_crossing(tau):
    if tau <= 0:
        raise ValueError('Positive time constant required')
    return tau*math.log(3)
