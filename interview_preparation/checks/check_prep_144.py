"""Independent nearest-frequency folding, sampled-tone and boundary examples."""
import importlib.util
import json
from fractions import Fraction
from itertools import product
from math import cos, pi, sin
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sampling_model", BANK / "solutions/prep_144_sampling_aliasing.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    folds = sample_points = 0
    for fs, f in product((16000, 20000, 24000, 48000, 96000), range(0, 200001, 125)):
        folded = model.folded_frequency(f, fs)
        # Oracle chooses the nearest integer multiple, without remainder folding.
        nearest = min(abs(Fraction(f) - k * fs) for k in range(15))
        assert folded == nearest and 0 <= folded <= Fraction(fs, 2)
        a = model.cosine_samples(f, fs, 17)
        b = [cos(2 * pi * float(folded) * n / fs) for n in range(17)]
        assert all(abs(x - y) < 2e-12 for x, y in zip(a, b, strict=True))
        sample_points += len(a)
        folds += 1
    # A 10 kHz sine at the 20 ksample/s boundary is invisible at phase zero.
    assert all(abs(sin(2 * pi * 10000 * n / 20000)) < 1e-12 for n in range(32))
    assert model.strict_baseband_rate_ok(10000, 48000)
    assert not model.strict_baseband_rate_ok(10000, 20000)
    high = model.cosine_samples(38000, 48000, 128)
    low = model.cosine_samples(10000, 48000, 128)
    assert all(abs(a - b) < 2e-12 for a, b in zip(high, low, strict=True))
    components = [(1000, 1), (10000, 1), (38000, Fraction(1, 2)), (96000, Fraction(1, 3))]
    kept = model.ideal_lowpass(components, 20000)
    assert kept == components[:2]
    assert all(model.folded_frequency(f, 48000) == f for f, _ in kept)
    rejected = 0
    for call in (lambda: model.folded_frequency(-1, 1), lambda: model.folded_frequency(1, 0),
                 lambda: model.ideal_lowpass([], -1), lambda: model.strict_baseband_rate_ok(-1, 1)):
        try:
            call()
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("invalid frequency contract accepted")
    return {"question_id": "PREP-144", "status": "passed", "frequency_folding_cases": folds,
            "sampled_cosine_comparisons": sample_points, "nyquist_boundary_zero_sine_samples": 32,
            "indistinguishable_38khz_10khz_samples_at_48ksps": 128, "ideal_filter_components": 4,
            "invalid_cases_rejected": rejected,
            "scope": "Mathematical tones, frequency folding and ideal brick-wall filtering only. No random-noise spectral guarantee, real filter design, ADC, jitter, quantization or hardware measurement."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-144-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
