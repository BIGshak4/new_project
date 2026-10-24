"""Independent charge-integration checks for the stated educational NMOS model."""
import importlib.util
import itertools
import json
from decimal import Decimal, localcontext
from math import isclose
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("nmos115", BANK / "solutions/prep_115_nmos_long_channel.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    cases = 0
    with localcontext() as context:
        context.prec = 60
        for gate, drain, threshold, beta in itertools.product(
            range(-2, 11), range(11), (1, 2, 3), ("0.0002", "0.001"),
        ):
            vg, vd, vt = (Decimal(value) / 4 for value in (gate, drain, threshold))
            strength = Decimal(beta)
            # Integrate the nonnegative inversion-charge factor over channel
            # potential. Midpoint integration is exact for this linear factor;
            # saturation truncates the integration where the charge reaches zero.
            stop = max(Decimal(0), min(vd, vg - vt))
            dv = stop / 32
            integral = sum(max(Decimal(0), vg - vt - (Decimal(k) + Decimal("0.5")) * dv) * dv
                           for k in range(32))
            expected = strength * integral
            region, actual = model.nmos_current(float(vg), float(vd), float(strength), float(vt))
            expected_region = "cutoff" if vg <= vt else "triode" if vd < vg - vt else "saturation"
            assert region == expected_region
            assert isclose(actual, float(expected), rel_tol=2e-14, abs_tol=1e-18)
            cases += 1
    clm = 0
    for overdrive, excess, channel_lambda in itertools.product((0.25, 0.5, 1.0), (0.0, 0.25, 0.75), (0.0, 0.1, 0.3)):
        baseline = model.nmos_current(0.5 + overdrive, overdrive, 0.001, 0.5)[1]
        current = model.saturation_with_clm(0.5 + overdrive, overdrive + excess, 0.001, 0.5, channel_lambda)
        assert isclose(current - baseline, baseline * channel_lambda * excess, abs_tol=1e-18)
        clm += 1
    # VDD is not a model input: two distinct explicit bias mappings matter.
    drain_only = [model.nmos_current(1.5, value, 0.001, 0.5)[1] for value in (1.0, 1.5, 2.0)]
    gate_only = [model.nmos_current(value, 2.0, 0.001, 0.5)[1] for value in (1.0, 1.5, 2.0)]
    assert len(set(drain_only)) == 1
    assert gate_only[0] < gate_only[1] < gate_only[2]
    invalid = ((1, -1, 0.001, 0.5), (1, 1, 0, 0.5), (1, 1, 0.001, 0), (float("nan"), 1, 0.001, 0.5))
    for arguments in invalid:
        try:
            model.nmos_current(*arguments)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid model input accepted")
    return {"status": "passed", "equation_grid_cases": cases, "clm_cases": clm,
            "explicit_supply_bias_examples": 2, "invalid_inputs_rejected": len(invalid),
            "oracle": "60-digit Decimal midpoint integration of channel charge, independently of the model's piecewise antiderivative",
            "scope": "Executed Python equation checks only; no SPICE/BSIM, process validation, device calibration, physical measurements or human professional review."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-115-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
