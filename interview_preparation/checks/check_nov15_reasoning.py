"""Finite independent checks for the Nov 15 knowledge, mass and circuit contracts."""
from fractions import Fraction
from itertools import product
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def knowledge_worlds():
    # An observer sees every coordinate except their own. Public silence
    # removes worlds in which any observer had already become certain.
    agents = 6
    verified = 0
    actual_four = None
    for minimum in range(1, agents + 1):
        possible = {mask for mask in range(1 << agents) if mask.bit_count() >= minimum}
        first_actions = {}
        for night in range(1, agents - minimum + 2):
            silent_worlds = set()
            for world in possible:
                acting = 0
                for observer in range(agents):
                    own_bit = 1 << observer
                    alternatives = [candidate for candidate in possible
                                    if candidate & ~own_bit == world & ~own_bit]
                    assert alternatives
                    if all(candidate & own_bit for candidate in alternatives):
                        acting |= own_bit
                if acting:
                    first_actions[world] = (night, acting)
                else:
                    silent_worlds.add(world)
            possible = silent_worlds
        assert not possible
        for world, (night, acting) in first_actions.items():
            assert night == world.bit_count() - minimum + 1
            assert acting == world
            verified += 1
            if minimum == 1 and world == 0b001111:
                actual_four = dict(first_action_night=night, acting_agents=acting.bit_count())
        assert len(first_actions) == sum(mask.bit_count() >= minimum for mask in range(1 << agents))
    return dict(agents=agents, verified_world_and_public_lower_bound_pairs=verified,
                actual_four=actual_four, method="Explicit indistinguishable worlds with public-silence updates")


def coin_bags():
    normal = Fraction(10)
    checks = 0
    for delta, offset, unusual in product(
            (Fraction(-2), Fraction(-1, 7), Fraction(1, 11), Fraction(3)),
            (0, 1), range(1, 11)):
        counts = [bag - offset for bag in range(1, 11)]
        # Form the complete coin multiset independently of the decoding formula.
        selected = [normal + (delta if bag == unusual else 0)
                    for bag, count in enumerate(counts, 1) for _ in range(count)]
        measured = sum(selected)
        baseline = sum(counts) * normal
        decoded = (measured - baseline) / delta + offset
        assert decoded.denominator == 1 and int(decoded) == unusual
        checks += 1
    assert sum(range(1, 11)) == 55 and sum(range(10)) == 45
    assert (Fraction(543) - 55 * normal) / -1 == 7
    return dict(exact_weight_cases=checks, signed_deviations=4, sample_schemes=2,
                method="Explicit coin multisets evaluated with exact rational arithmetic")


def load_power():
    checked = 0
    ratios = [Fraction(i, 20) for i in range(1, 101)] + [Fraction(1, 10**6), Fraction(10**6)]
    for supply, r1, r2 in product((Fraction(1), Fraction(12), Fraction(48)),
                                   (Fraction(1), Fraction(500), Fraction(1000), Fraction(1500)),
                                   (Fraction(2), Fraction(2000), Fraction(4700))):
        vth = supply * r2 / (r1 + r2)
        rth = 1 / (1 / r1 + 1 / r2)
        maximum = vth * vth / (4 * rth)
        for ratio in ratios:
            load = ratio * rth
            # Solve Kirchhoff's node equation rather than evaluating the
            # Thevenin voltage-divider expression as the reference.
            output = (supply / r1) / (1 / r1 + 1 / r2 + 1 / load)
            power = output * output / load
            assert power == vth * vth * load / (rth + load)**2
            assert power <= maximum
            assert (power == maximum) == (ratio == 1)
            source_power = supply * (supply - output) / r1
            dissipation = (supply - output)**2 / r1 + output**2 / r2 + power
            assert source_power == dissipation
            checked += 1
    supply, r1, r2 = Fraction(12), Fraction(1000), Fraction(2000)
    rth = 1 / (1 / r1 + 1 / r2)
    vth = supply * r2 / (r1 + r2)
    maximum = vth * vth / (4 * rth)
    output = Fraction(4)
    total = supply * (supply - output) / r1
    assert maximum == Fraction(24, 1000)
    assert maximum / total == Fraction(1, 4)
    energy_tests = 0
    steps = 20000
    stop = 40.0
    du = stop / steps
    for capacitance in (1e-9, 1e-6, 1e-3):
        tau = float(rth) * capacitance
        # Integrate instantaneous v(t)*i(t) with a trapezoidal sum.
        samples = []
        for index in range(steps + 1):
            time = index * du * tau
            voltage = float(vth) * (1 - math.exp(-time / tau))
            current = float(vth / rth) * math.exp(-time / tau)
            samples.append(voltage * current)
        energy = du * tau * (sum(samples) - (samples[0] + samples[-1]) / 2)
        expected = .5 * capacitance * float(vth)**2
        assert math.isclose(energy, expected, rel_tol=1e-6)
        peak_time = tau * math.log(2)
        at_peak = float(vth * vth / rth) * math.exp(-peak_time / tau) * (1 - math.exp(-peak_time / tau))
        assert math.isclose(at_peak, float(maximum), rel_tol=1e-12)
        energy_tests += 1
    return dict(nodal_and_thevenin_cases=checked, capacitor_energy_integrals=energy_tests,
                integration_steps_per_capacitance=steps, maximum_watts=float(maximum),
                divider_efficiency=.25, method="Exact nodal solution and numerical energy integration")


def main():
    result = dict(result="passed", knowledge=knowledge_worlds(), coin_bags=coin_bags(),
                  power=load_power(), scope="Finite mathematical models, without physical circuit measurements")
    files = [Path(__file__), *sorted((ROOT / "diagrams").glob("prep-34[345]-*.png"))]
    result["verified_source_sha256"] = {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in files}
    target = ROOT / "checks/batch1115-reasoning-verification.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({key: value for key, value in result.items() if key != "verified_source_sha256"}))


if __name__ == "__main__":
    main()
