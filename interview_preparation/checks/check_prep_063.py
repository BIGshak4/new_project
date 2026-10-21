"""Numerical geometry checks; the analytic inequalities provide the proof."""
import importlib.util
import json
from math import acos, cos, pi, sin, isclose
from pathlib import Path
import random

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("duck_fox", BANK / "solutions/prep_063_duck_fox.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run():
    scales = 0
    for radius in (0.01, 1, 7.5, 1000):
        for speed in (0.01, 0.5, 1, 20):
            bound = module.strategy_bounds(radius, speed)
            assert 0 < bound["orbit_radius"] < radius/4
            assert bound["angular_advantage"] > 0
            assert bound["strict_time_margin"] > 0
            assert isclose(bound["radial_sprint_time"]/(radius/speed), 19/25)
            assert isclose(bound["fox_earliest_endpoint_time"]/(radius/speed), pi/4)
            scales += 1
    # Independent coordinates: opposite shore vectors have shortest arc piR.
    endpoint_samples = 0
    radius = 7.0
    for i in range(720):
        angle = 2*pi*i/720
        fox = (radius*cos(angle), radius*sin(angle))
        goal = (-fox[0], -fox[1])
        dot = (fox[0]*goal[0]+fox[1]*goal[1])/(radius*radius)
        shortest_arc = radius*acos(max(-1, min(1, dot)))
        assert isclose(shortest_arc, pi*radius, rel_tol=1e-8)
        endpoint_samples += 1
    alignments = 0
    bounds = module.strategy_bounds()
    for i in range(201):
        gap = -pi + 2*pi*i/200
        for j in range(41):
            fox_velocity = -4 + 8*j/40
            t = module.alignment_time(gap, fox_velocity)
            assert -1e-12 <= t <= bounds["alignment_time_upper_bound"] + 1e-10
            direction = module.orbit_direction(gap)
            final = gap + (direction*bounds["duck_angular_speed"]-fox_velocity)*t
            assert isclose(abs(final), pi, rel_tol=1e-9)
            alignments += 1
    # Piecewise adversarial bounded motion, integrated exactly on each segment.
    # Duck chooses direction once; the signed separation then grows monotonically.
    piecewise = 0
    for seed in range(200):
        rng = random.Random(seed)
        gap = rng.uniform(-pi, pi)
        direction = module.orbit_direction(gap)
        progress = abs(gap)
        elapsed = 0.0
        for _ in range(5000):
            velocity = rng.uniform(-4, 4)
            duration = rng.uniform(0.001, 0.2)
            relative = bounds["duck_angular_speed"]-direction*velocity
            assert relative >= bounds["angular_advantage"]-1e-12
            needed = (pi-progress)/relative
            if needed <= duration:
                elapsed += needed
                assert elapsed <= bounds["alignment_time_upper_bound"] + 1e-9
                piecewise += 1
                break
            progress += relative*duration
            elapsed += duration
        else:
            raise AssertionError("Piecewise alignment test did not finish")
    # Center-only radial sprint is NOT the proposed strategy.
    assert 1 > pi/4
    assert isclose(bounds["strict_time_margin"], pi/4-19/25)
    result = {
        "question_id": "PREP-063", "status": "passed", "scale_checks": scales,
        "independent_opposite_endpoint_coordinate_checks": endpoint_samples,
        "constant_velocity_alignment_checks": alignments,
        "piecewise_bounded_adversary_samples": piecewise,
        "orbit_fraction": "6/25", "normalized_angular_advantage": "1/6",
        "normalized_sprint_time": "19/25 =0.76", "fox_best_endpoint_time": "pi/4 ≈0.785398",
        "strict_margin": bounds["strict_time_margin"],
        "limits": "Numerical samples check formulas and geometry; universal correctness follows from the written speed inequalities, not finite simulation. Fox restricted to shore, continuous observation, ideal point agents, arbitrary turns and immediate escape at shore are assumptions. No physical trial or optimality claim.",
    }
    (BANK / "checks/prep-063-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
