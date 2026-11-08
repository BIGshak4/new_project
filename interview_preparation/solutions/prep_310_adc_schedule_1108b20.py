"""Rate/timestamp/settling model, not an ADC or analog reconstruction simulator."""
from fractions import Fraction as F


def per_channel_rate(adc_rate, channels=4):
    if adc_rate <= 0 or type(channels) is not int or channels <= 0:
        raise ValueError('Positive rate and integer channel count required')
    return F(adc_rate)/channels


def round_robin(adc_rate=1_000_000, slots=16):
    if type(slots) is not int or slots < 0 or adc_rate <= 0:
        raise ValueError('Nonnegative slot count and positive rate required')
    return [(k%4,F(k,adc_rate)) for k in range(slots)]


def slot_fits(switch_s, acquisition_s, conversion_s, adc_rate):
    times=list(map(F,(switch_s,acquisition_s,conversion_s)))
    if min(times)<0 or adc_rate<=0:
        raise ValueError('Nonnegative times and positive rate required')
    return sum(times)<=F(1,adc_rate)


def settling_time(tau, previous_full_scale, allowed_error):
    """Ideal first-order acquisition residual: delta*exp(-t/tau)."""
    import math
    if tau<=0 or not 0 < allowed_error < previous_full_scale:
        raise ValueError('Require tau>0 and 0<error<step')
    return tau*math.log(previous_full_scale/allowed_error)
