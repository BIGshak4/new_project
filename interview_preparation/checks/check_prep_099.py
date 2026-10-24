"""Verify RC inference with Decimal network arithmetic and independent KCL integration."""

import importlib.util
import itertools
import json
from decimal import Decimal, localcontext
from math import inf, isclose
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("capacitance", BANK / "solutions/prep_099_rc_capacitance.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def rk4_voltage(source, series, shunt, total_cap, initial, duration, steps=8000):
    """Integrate KCL currents directly; do not evaluate an exponential or tau."""
    dt = duration / steps

    def derivative(voltage):
        source_current = (source - voltage) / series
        probe_current = 0 if shunt == inf else voltage / shunt
        return (source_current - probe_current) / total_cap

    voltage = initial
    for _ in range(steps):
        k1 = derivative(voltage)
        k2 = derivative(voltage + dt * k1 / 2)
        k3 = derivative(voltage + dt * k2 / 2)
        k4 = derivative(voltage + dt * k3)
        voltage += dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6
    return voltage


def run_checks():
    network_cases = 0
    with localcontext() as ctx:
        ctx.prec = 70
        for r, c, rs, rp, cp in itertools.product(
            ("10", "1000", "10000", "1000000"),
            ("1e-12", "1e-9", "1e-6", "1e-3"),
            ("0", "50"), (None, "1e6", "1e7"), ("0", "1e-11"),
        ):
            resistance, capacitance, source, parasitic = map(Decimal, (r, c, rs, cp))
            series = resistance + source
            shunt = Decimal(rp) if rp else None
            conductance = 1 / series + (1 / shunt if shunt else Decimal(0))
            # Physical conductance/capacitance equation generated independently.
            tau = (capacitance + parasitic) / conductance
            inferred = model.infer_capacitance(
                float(resistance), float(tau), source_ohm=float(source),
                probe_ohm=float(shunt) if shunt else inf, probe_farad=float(parasitic),
            )
            assert isclose(inferred, float(capacitance), rel_tol=5e-14)
            for elapsed_ratio in (Decimal(0), Decimal("0.5"), Decimal(1), Decimal(2), Decimal(5)):
                expected = Decimal(1) - (-elapsed_ratio).exp()
                actual = model.transition_voltage(float(elapsed_ratio * tau), float(tau))
                assert isclose(actual, float(expected), rel_tol=2e-14, abs_tol=2e-15)
            network_cases += 1

    integrated = 0
    for series, shunt, capacitance, initial, final_source in itertools.product(
        (1000, 10050), (inf, 1e6), (1e-9, 1e-6), (0, 0.2), (1,),
    ):
        conductance = 1 / series + (0 if shunt == inf else 1 / shunt)
        tau = capacitance / conductance
        plateau = final_source if shunt == inf else final_source * shunt / (series + shunt)
        for multiple in (1, 3, 5):
            numerical = rk4_voltage(final_source, series, shunt, capacitance,
                                    initial, multiple * tau)
            analytic = model.transition_voltage(multiple * tau, tau, initial, plateau)
            assert isclose(numerical, analytic, rel_tol=2e-11, abs_tol=2e-12)
            integrated += 1

    assert isclose(model.infer_capacitance(10000, 0.001), 100e-9, rel_tol=1e-14)
    assert isclose(model.transition_voltage(0.001, 0.001), 0.6321205588285577, rel_tol=1e-14)
    assert isclose(model.transition_voltage(0.001, 0.001, 1, 0), 0.36787944117144233, rel_tol=1e-14)
    # Loading is not harmless: half the series resistance yields a different tau,
    # and a probe capacitance equal to C doubles the observed total capacitance.
    assert model.effective_resistance(1000, probe_ohm=1000) == 500
    assert isclose(model.infer_capacitance(1000, 2e-6, probe_farad=1e-9), 1e-9,
                   rel_tol=1e-14)
    rejected = 0
    invalid_inference = [
        (0, 1, {}), (-1, 1, {}), (inf, 1, {}), (1000, 0, {}),
        (1000, float("nan"), {}), (1000, 1, {"source_ohm": -1}),
        (1000, 1, {"probe_ohm": 0}), (1000, 1, {"probe_farad": -1}),
        (1000, 1e-6, {"probe_farad": 2e-9}),
    ]
    for r, tau, kwargs in invalid_inference:
        try:
            model.infer_capacitance(r, tau, **kwargs)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError((r, tau, kwargs))
    for time, tau, v0, vinf in ((-1, 1, 0, 1), (0, 0, 0, 1), (1, 1, inf, 1)):
        try:
            model.transition_voltage(time, tau, v0, vinf)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError((time, tau, v0, vinf))
    return {
        "question_id": "PREP-099", "status": "passed",
        "network_inference_cases": network_cases,
        "decimal_transition_checks": network_cases * 5,
        "independent_kcl_rk4_cases": integrated,
        "rk4_steps_per_case": 8000, "invalid_cases_rejected": rejected,
        "example_capacitance_farad": model.infer_capacitance(10000, 0.001),
        "scope": "Ideal lumped first-order RC network; Decimal algebra and independent KCL/RK4 numerical integration. No physical measurement, instrument calibration or fitted uncertainty claim.",
    }


if __name__ == "__main__":
    evidence = run_checks()
    (BANK / "checks/prep-099-verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))
