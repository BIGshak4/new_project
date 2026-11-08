"""Chosen interpretation is sin(2*pi*n/32), not the literal *32."""
import math

QUARTER=[0,6393,12539,18204,23170,27245,30273,32137,32767]


def sample(phase):
    if type(phase) is not int or not 0<=phase<32:
        raise ValueError('phase0..31 required')
    q=phase%16
    index=min(q,16-q)
    magnitude=QUARTER[index]
    return -magnitude if phase>=16 else magnitude


def full_table():
    return [round(32767*math.sin(2*math.pi*n/32)) for n in range(32)]
