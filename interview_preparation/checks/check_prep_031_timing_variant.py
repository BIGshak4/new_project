"""Truth-table, delayed-net and independent arrival/deadline checks."""

import importlib.util
import json
from fractions import Fraction
from itertools import product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mux_timing", BANK / "solutions/prep_031_timing_variant.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def delayed_output(old, new, gate_delay=2):
    """Independent sampled transport model, using direct Boolean expressions.

    All inputs are settled before tick zero. Each cell looks back by its delay.
    No characterization, analog glitches or rise/fall asymmetry is asserted.
    """
    def input_at(index, time):
        return new[index] if time >= 0 else old[index]

    def inner(time):
        return int(bool(input_at(0, time - gate_delay)) and not input_at(1, time - gate_delay))

    def output(time):
        past = time - gate_delay
        return inner(past) if input_at(0, past) else input_at(1, past)

    values = [output(t) for t in range(2 * gate_delay + 2)]
    final = int(new[0] != new[1])
    settling = next(t for t in range(len(values)) if all(x == final for x in values[t:]))
    return settling, values


def run_checks():
    truth = transitions = timing = hold_cases = rejected = 0
    worst = 0
    for a, b in product((0, 1), repeat=2):
        assert model.xor_zero_only(a, b) == int(a != b)
        truth += 1
        for changed in range(2):
            new = [a, b]
            new[changed] ^= 1
            settling, values = delayed_output((a, b), tuple(new))
            assert values[-1] == int(new[0] != new[1])
            assert settling <= 4
            worst = max(worst, settling)
            transitions += 1
    assert worst == 4
    assert model.maximum_frequency_hz(2) == 500_000_000
    assert model.maximum_frequency_hz(4) == 250_000_000
    for path, cq, setup, skew, uncertainty in product(
        (Fraction(2), Fraction(4)), (Fraction(0), Fraction(1, 5)),
        (Fraction(0), Fraction(3, 10)), (Fraction(-1, 5), Fraction(0), Fraction(1, 5)),
        (Fraction(0), Fraction(1, 10))
    ):
        period = model.required_period_ns(path, clock_to_q=cq, setup=setup, skew=skew, uncertainty=uncertainty)
        # Absolute launch at 7 ns: arrival must precede the capture setup deadline.
        arrival = Fraction(7) + cq + path
        deadline = Fraction(7) + period + skew - setup - uncertainty
        assert arrival == deadline
        assert arrival > deadline - Fraction(1, 1000)
        assert arrival < deadline + Fraction(1, 1000)
        timing += 1
    for contamination, cq_min, hold, skew in product(
        (Fraction(0), Fraction(1, 10), Fraction(1, 2)),
        (Fraction(0), Fraction(1, 10)), (Fraction(0), Fraction(1, 5)),
        (Fraction(-1, 5), Fraction(0), Fraction(1, 5))
    ):
        arrival = Fraction(7) + cq_min + contamination
        deadline = Fraction(7) + skew + hold
        assert model.hold_is_met(contamination, clock_to_q_min=cq_min, hold=hold, skew=skew) == (arrival >= deadline)
        hold_cases += 1
    for args in [(0, {}), (-1, {}), (2, {"clock_to_q": -1}),
                 (2, {"setup": -1}), (2, {"uncertainty": -1}), (2, {"skew": 3})]:
        try:
            model.required_period_ns(args[0], **args[1])
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(args)
    for value in (-1, 2, True):
        try:
            model.xor_zero_only(value, 0)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(value)
    return {"question_id": "PREP-031", "variant": "batch30_timing", "status": "passed",
            "xor_truth_rows": truth, "single_input_transition_cases": transitions,
            "worst_transport_delay_ns": worst, "setup_arrival_deadline_cases": timing,
            "hold_arrival_deadline_cases": hold_cases, "invalid_cases_rejected": rejected,
            "scope": "Exact rational timing and ideal equal-delay transport model; not STA, HDL simulation or characterized hardware."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-031-timing-variant-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
