"""Compare safe-rate intervals against reflected spectral-image overlap."""
import importlib.util
import json
import math
from fractions import Fraction
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('band156', BANK/'solutions/prep_156_bandpass_rate_intervals.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def spectral_oracle(low, high, rate):
    # A real band has both positive and negative support. Test all possibly
    # intersecting periodic copies against the original positive support.
    for sign in (1, -1):
        left, right = (low, high) if sign == 1 else (-high, -low)
        for k in range(-int(2*high/rate)-2, int(2*high/rate)+3):
            if sign == 1 and k == 0:
                continue
            if max(low, left+k*rate) <= min(high, right+k*rate):
                return False
    return True


def verify():
    cases = 0
    for low in range(1, 13):
        for high in range(low+1, 18):
            for twice_rate in range(2, 101):
                rate = Fraction(twice_rate, 2)
                assert model.is_safe_rate(low, high, rate) == spectral_oracle(low, high, rate), (low,high,rate)
                cases += 1
    assert model.safe_intervals(90,110)[-1] == (5,Fraction(44),Fraction(45))
    assert model.is_safe_rate(90,110,Fraction(89,2))
    assert not model.is_safe_rate(90,110,40)
    assert not model.is_safe_rate(90,110,44)
    # A degenerate nominal interval is unsafe for arbitrary endpoint tones.
    assert model.safe_intervals(100,120)[-1] == (5,Fraction(48),Fraction(50))
    assert not model.is_safe_rate(100,120,40)
    assert model.is_safe_rate(0,10,21) and not model.is_safe_rate(0,10,20)
    samples = 0
    rate = Fraction(89,2)
    for frequency in range(90,111):
        alias = model.fold_frequency(frequency,rate)
        for n in range(25):
            assert abs(math.cos(2*math.pi*float(frequency/rate)*n) - math.cos(2*math.pi*float(alias/rate)*n)) < 1e-10
            samples += 1
    # At a Nyquist endpoint, a nonzero sine can yield identically zero samples.
    assert all(abs(math.sin(2*math.pi*110*n/44)) < 1e-10 for n in range(25))
    return {'status':'passed','spectral_overlap_cases':cases,'alias_cosine_samples':samples,
            'endpoint_phase_counterexample_samples':25,
            'scope':'Exact rational spectral geometry and numerical tones; not a physical ADC/filter experiment.'}


if __name__ == '__main__':
    result = verify()
    (BANK/'checks/prep-156-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result)
