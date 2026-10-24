"""Independent interval and history checks for analog decision contracts."""
import importlib.util
import itertools
import json
from decimal import Decimal
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("threshold118", BANK / "solutions/prep_118_analog_threshold.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    decisions = 0
    for reference, offset, uncertainty in itertools.product(("-1", "0", "1.25"), range(-12, 13), ("0", "0.125", "0.25")):
        ref, delta, margin = Decimal(reference), Decimal(offset) / 8, Decimal(uncertainty)
        interval = (delta - margin, delta + margin)
        expected = 1 if min(interval) > 0 else 0 if max(interval) < 0 else None
        assert model.compare_voltage(float(ref + delta), float(ref), float(margin)) == expected
        decisions += 1
    streams = steps = 0
    for length in range(6):
        for initial in (None, 0, 1):
            for samples in itertools.product((-1.0, -0.5, 0.0, 0.5, 1.0), repeat=length):
                state = initial
                for end, value in enumerate(samples, 1):
                    # Independent history oracle: only the most recent strict
                    # excursion outside the band can decide a new stored state.
                    events = [sample for sample in samples[:end] if abs(sample) > 0.5]
                    expected = int(events[-1] > 0) if events else initial
                    state = model.schmitt_step(value, -0.5, 0.5, state)
                    assert state == expected
                    steps += 1
                streams += 1
    noisy = [1.25 - 0.02, 1.25 + 0.02] * 8
    plain = [model.compare_voltage(value, 1.25) for value in noisy]
    state, hysteretic = 0, []
    for value in noisy:
        state = model.schmitt_step(value, 1.2, 1.3, state)
        hysteretic.append(state)
    assert sum(a != b for a, b in itertools.pairwise(plain)) == 15
    assert hysteretic == [0] * 16
    assert model.compare_voltage(1.25, 1.25) is None
    assert model.schmitt_step(1.25, 1.2, 1.3, None) is None
    invalid = 0
    for function, arguments in ((model.compare_voltage, (0, 0, -1)),
                                (model.compare_voltage, (float("inf"), 0)),
                                (model.schmitt_step, (0, 1, 1, 0)),
                                (model.schmitt_step, (0, -1, 1, 2))):
        try:
            function(*arguments)
        except ValueError:
            invalid += 1
        else:
            raise AssertionError("invalid decision contract accepted")
    return {"status": "passed", "interval_decisions": decisions, "hysteresis_streams": streams,
            "history_steps": steps, "noise_demo_samples": 16, "invalid_inputs_rejected": invalid,
            "oracle": "Decimal uncertainty intervals and the most recent strict band-excursion history",
            "scope": "Executed settled Python decision/state models only. No analog simulator, component selection, hardware measurement, timing or immunity guarantee; human professional review pending."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-118-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
