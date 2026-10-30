"""Educational DC roots checked against independent closed-form branches."""

import importlib.util
import itertools
import json
from math import isclose, sqrt
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "inverter153", BANK / "solutions/prep_153_nmos_load_inverter.py"
)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    exact_high = exact_low = body_cases = depletion_cases = 0
    for vdd, vt, ratio in itertools.product((2.5, 3.3, 5.0), (0.4, 0.7, 1.0), (4.0, 8.0, 16.0)):
        params = {"vdd": vdd, "driver_threshold": vt, "load_threshold": vt, "beta_driver": ratio}
        assert isclose(model.dc_output(0.0, **params), vdd - vt, rel_tol=1e-12, abs_tol=1e-12)
        exact_high += 1
        # Independent quadratic solution under saturated load/triode driver.
        overdrive = vdd - vt
        a = 1 + ratio
        b = -2 * overdrive * (1 + ratio)
        c = overdrive**2
        root = (-b - sqrt(b * b - 4 * a * c)) / (2 * a)
        assert 0 <= root < overdrive
        actual = model.dc_output(vdd, **params)
        assert isclose(actual, root, rel_tol=1e-12, abs_tol=1e-12)
        exact_low += 1
    for gamma in (0.2, 0.4, 0.8):
        previous = 6.0
        for i in range(101):
            vin = i / 20
            output = model.dc_output(vin, gamma=gamma)
            iload, idriver = model.currents(vin, output, gamma=gamma)
            assert 0 <= output <= 5 and abs(iload - idriver) < 1e-10
            assert output <= previous + 1e-12
            previous = output
            body_cases += 1
        high = model.dc_output(0.0, gamma=gamma)
        assert high < 4.0
        # Independent body-threshold boundary identity, charging from below.
        assert isclose(high + 1 + gamma * (sqrt(0.6 + high) - sqrt(0.6)), 5.0, abs_tol=1e-12)
    for ratio in (4.0, 8.0, 16.0):
        params = {"load_kind": "depletion", "load_threshold": -0.5, "beta_driver": ratio}
        assert isclose(model.dc_output(0.0, **params), 5.0, abs_tol=1e-12)
        load_sat = 0.5 * 0.5 / 2
        expected = 4 - sqrt(16 - 2 * load_sat / ratio)
        assert isclose(model.dc_output(5.0, **params), expected, abs_tol=1e-12)
        depletion_cases += 2
    weak = model.dc_output(5.0, beta_driver=1.0)
    strong = model.dc_output(5.0, beta_driver=16.0)
    assert 0 < strong < weak
    static_current = model.currents(5.0, strong, beta_driver=16.0)[0]
    assert static_current > 0
    return {
        "question_id": "PREP-153",
        "status": "passed",
        "enhancement_high_analytic_cases": exact_high,
        "enhancement_low_quadratic_cases": exact_low,
        "body_effect_sweep_cases": body_cases,
        "depletion_analytic_cases": depletion_cases,
        "sizing_static_current_witnesses": 2,
        "illustration_vdd": 5.0,
        "illustration_vt": 1.0,
        "illustration_beta_ratio": 8.0,
        "illustration_voh_no_body": model.dc_output(0.0),
        "illustration_vol_no_body": model.dc_output(5.0),
        "illustration_voh_body_gamma_point_four": model.dc_output(0.0, gamma=0.4),
        "scope": "Long-channel square-law Python illustration, checked against closed-form high and low roots and Kirchhoff current balance. No SPICE, process parameters, fabricated measurement or guaranteed noise margins; cutoff high denotes charging from below in an ideal leakage-free model.",
    }


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-153-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))
