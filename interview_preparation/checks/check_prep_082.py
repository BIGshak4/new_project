"""Independent bounds and sampled quadrature checks; no physical experiment."""
import importlib.util
import json
from math import isclose, pi, sin, sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("tracks", ROOT / "solutions/prep_082_mirrored_tracks.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def riemann_bounds(height, radius, dip, gravity, steps=2048):
    """On half an arc sin increases, giving monotone upper/lower time sums."""
    width = pi / (2 * steps)
    values = [radius / sqrt(2 * gravity * (height + (1 if dip else -1) * radius * sin(i * width)))
              for i in range(steps + 1)]
    left = 2 * width * sum(values[:-1])
    right = 2 * width * sum(values[1:])
    return min(left, right), max(left, right)


def main():
    cases = speed_cases = 0
    for ratio in (1.01, 1.1, 1.5, 2, 5, 10):
        for radius in (0.1, 1.0, 3.0):
            for gravity in (1.0, 9.81, 20.0):
                height = ratio * radius
                hill = model.feature_time(height, radius, gravity=gravity)
                dip = model.feature_time(height, radius, dip=True, gravity=gravity)
                h_lo, h_hi = riemann_bounds(height, radius, False, gravity)
                d_lo, d_hi = riemann_bounds(height, radius, True, gravity)
                assert h_lo <= hill <= h_hi and d_lo <= dip <= d_hi
                assert d_hi < h_lo, "Independent travel-time intervals must be disjoint"
                assert isclose(hill, model.feature_time(height, radius, gravity=gravity, intervals=8192), rel_tol=1e-9)
                assert isclose(dip, model.feature_time(height, radius, dip=True, gravity=gravity, intervals=8192), rel_tol=1e-9)
                for i in range(1, 100):
                    altitude = radius * sin(pi * i / 100)
                    assert model.speed(height, -altitude, gravity) > model.speed(height, altitude, gravity)
                    speed_cases += 1
                baseline = sqrt(2 * gravity * height)
                assert model.speed(height, 0, gravity) == baseline
                cases += 1
    rejected = 0
    for args in ((1, 1), (0.5, 1), (2, 0), (2, -1)):
        try:
            model.feature_time(*args)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(args)
    evidence = {
        "status": "passed", "parameter_combinations": cases,
        "interior_speed_comparisons": speed_cases, "invalid_geometry_rejections": rejected,
        "example_H3_R1_g9_81_seconds": {"hill": model.feature_time(3, 1), "dip": model.feature_time(3, 1, dip=True)},
        "independent_oracle": "Monotone half-arc Riemann bounds, separate from Simpson quadrature",
        "proof": "At paired arc lengths the dip has lower altitude, greater speed and strictly smaller time integrand.",
        "scope": "Ideal guided point masses with H>R2 and mirrored equal-length features; not real rolling/contact validation.",
    }
    (ROOT / "checks/prep-082-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()
