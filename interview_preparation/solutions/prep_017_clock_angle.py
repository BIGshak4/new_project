"""Exact arithmetic for a conventional continuously moving 12-hour clock."""
from fractions import Fraction

def hand_angles(hour,minute):
    if not isinstance(hour,int) or not isinstance(minute,int):
        raise TypeError('Hour and minute must be integers')
    if not 0<=hour<=23 or not 0<=minute<60:
        raise ValueError('Expected hour 0..23 and minute 0..59')
    hour_angle=30*(hour%12)+Fraction(minute,2)
    minute_angle=6*minute
    return hour_angle,minute_angle

def smaller_angle(hour,minute):
    h,m=hand_angles(hour,minute)
    delta=abs(h-m)
    return min(delta,360-delta)
