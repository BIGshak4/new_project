"""Check geometric and long-channel teaching models with independent calculations."""

import hashlib
import json
import sys
from cmath import exp
from decimal import Decimal, localcontext
from math import acos, cos, isclose, pi, radians, tau
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / 'solutions'))
from prep_366_receive_phase import observed_phase, projected_path, recover_angle
from prep_367_nmos_mirror import output_current, reference_current_at_knee


def check_geometry() -> dict:
    distances_checked = 0
    inversions_checked = 0
    with localcontext() as context:
        context.prec = 60
        range_to_midpoint = Decimal(1000000)
        for spacing in (0.005, 0.05, 0.12, 0.4):
            half_spacing = Decimal(str(spacing)) / 2
            for degree in range(0, 181, 5):
                angle = radians(degree)
                sx = Decimal(str(cos(angle))) * range_to_midpoint
                # Cartesian source coordinates at the chosen distance from the midpoint.
                sy_squared = range_to_midpoint ** 2 - sx ** 2
                r1 = ((sx - half_spacing) ** 2 + sy_squared).sqrt()
                r2 = ((sx + half_spacing) ** 2 + sy_squared).sqrt()
                assert isclose(float(r2 - r1), projected_path(spacing, angle), rel_tol=1e-12, abs_tol=1e-15)
                distances_checked += 1
    for wavelength in (0.15, 0.30, 1.2):
        for relative_spacing in (0.01, 0.125, 0.4, 0.499):
            spacing = relative_spacing * wavelength
            for degree in range(181):
                angle = radians(degree)
                phase = observed_phase(spacing, angle, wavelength)
                assert isclose(angle, recover_angle(spacing, phase, wavelength), abs_tol=2e-7)
                inversions_checked += 1
        assert observed_phase(wavelength / 2, 0, wavelength) == -pi
        assert observed_phase(wavelength / 2, pi, wavelength) == -pi
        assert observed_phase(0, 0, wavelength) == observed_phase(0, pi, wavelength) == 0
        for relative_spacing in (0.501, 0.75, 2.0):
            positive_angle = acos(1 / (2 * relative_spacing))
            negative_angle = pi - positive_angle
            first = observed_phase(relative_spacing * wavelength, positive_angle, wavelength)
            second = observed_phase(relative_spacing * wavelength, negative_angle, wavelength)
            # Compare on the circle so +pi and -pi roundoff use the same point.
            assert abs(exp(1j * first) - exp(1j * second)) < 1e-13
    example_phase = observed_phase(0.12, pi / 3, 0.30)
    assert isclose(example_phase, tau / 5)
    assert observed_phase(0.12, pi / 3, 0.30) > 0
    assert observed_phase(0.12, 2 * pi / 3, 0.30) < 0
    return dict(distance_projections=distances_checked, unique_inversions=inversions_checked,
                half_wavelength_collisions=3, interior_collisions_above_half_wavelength=9)


def check_mirror() -> dict:
    samples = 0
    voltage_limits = (0, 0.25, 0.5, 0.75, 1.0, 1.5)
    for beta_ref, beta_out in ((1.0, 2.0), (0.5, 0.5), (1.75, 3.5)):
        for voltage in voltage_limits:
            previous = 0.0
            for step in range(201):
                current = step / 400
                threshold = 0.5
                gate_voltage = threshold + (2 * current / beta_ref) ** 0.5
                # Integrate the linear inversion-charge profile from the source
                # to clamp(Vout, VOV) using midpoint quadrature, exact for a line.
                end = min(voltage, gate_voltage - threshold)
                dx = end / 32
                oracle = sum(beta_out * (gate_voltage - threshold - (i + 0.5) * dx) * dx for i in range(32))
                measured = output_current(current, voltage, beta_ref, beta_out)
                assert isclose(oracle, measured, rel_tol=1e-11, abs_tol=1e-14)
                assert previous <= measured + 1e-14
                assert 0 <= measured <= current * beta_out / beta_ref + 1e-14
                if voltage >= gate_voltage - threshold:
                    assert isclose(measured, current * beta_out / beta_ref, abs_tol=1e-14)
                previous = measured
                samples += 1
    example_points = []
    for voltage, in_knee, out_knee, final in ((0.25, 0.03125, 0.0625, 0.4375), (0.75, 0.28125, 0.5625, 0.9375)):
        assert reference_current_at_knee(voltage) == in_knee
        assert output_current(in_knee, voltage) == out_knee
        assert output_current(0.5, voltage) == final
        assert abs(output_current(in_knee + 1e-9, voltage) - output_current(in_knee - 1e-9, voltage)) < 1e-8
        example_points.append(dict(voltage=voltage, knee_input_mA=in_knee, knee_output_mA=out_knee, output_at_0_5mA=final))
    return dict(transfer_samples=samples, example_points=example_points)


def check_invalid_inputs() -> int:
    invalid = (
        lambda: observed_phase(0.12, 1.0, 0), lambda: projected_path(-0.12, 1.0),
        lambda: projected_path(0.12, -1.0), lambda: recover_angle(0.15, 0.1, 0.30),
        lambda: recover_angle(0.03, 3, 0.30), lambda: output_current(-1, 0.25),
        lambda: output_current(0.5, -0.25), lambda: output_current(0.5, 0.25, beta_output=0),
        lambda: reference_current_at_knee(float('inf')),
    )
    for operation in invalid:
        try:
            operation()
        except ValueError:
            continue
        raise AssertionError('invalid model input was accepted')
    return len(invalid)


def main() -> None:
    report = dict(status='passed', question_ids=['PREP-366', 'PREP-367'],
                  geometry=check_geometry(), mirror=check_mirror(), invalid_inputs=check_invalid_inputs(),
                  human_expert_review=False,
                  scope='Plane-wave geometry, wrapped phase, and ideal long-channel equation checks. No RF measurements or SPICE simulation.')
    files = ['solutions/prep_366_receive_phase.py', 'solutions/prep_367_nmos_mirror.py', 'checks/check_analog1118.py']
    report['source_sha256'] = {name: hashlib.sha256((BANK / name).read_bytes()).hexdigest() for name in files}
    path = BANK / 'checks/analog1118-verification.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8', newline='\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
