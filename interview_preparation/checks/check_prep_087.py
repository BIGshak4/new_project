"""Independent winding and analytic shape checks for PREP-087."""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solutions"))
from prep_087_point_in_polygon import point_in_polygon


def winding_oracle(poly, p):
    """Signed winding, independently written; not crossing-parity code."""
    winding = 0
    x, y = p
    for j in range(len(poly)):
        x1, y1 = poly[j]
        x2, y2 = poly[(j + 1) % len(poly)]
        determinant = x1 * y2 + x2 * y + x * y1 - y1 * x2 - y2 * x - y * x1
        if determinant == 0 and (x - x1) * (x - x2) <= 0 and (y - y1) * (y - y2) <= 0:
            return "boundary"
        if y1 <= y < y2 and determinant > 0:
            winding += 1
        elif y2 <= y < y1 and determinant < 0:
            winding -= 1
    return "inside" if winding else "outside"


def on_supporting_line(poly, p):
    x, y = p
    return any((b[0] - a[0]) * (y - a[1]) == (b[1] - a[1]) * (x - a[0])
               for a, b in zip(poly, poly[1:] + poly[:1]))


def histogram(heights):
    """Simple orthogonal polygon above y=0 with unit-width columns."""
    points = [(0, 0), (len(heights), 0), (len(heights), heights[-1])]
    for i in range(len(heights) - 1, -1, -1):
        points.append((i, heights[i]))
        if i and heights[i - 1] != heights[i]:
            points.append((i, heights[i - 1]))
    return points


def run():
    fixtures = [
        [(0, 0), (8, 0), (8, 8), (0, 8)],
        [(0, 0), (8, 0), (8, 2), (3, 2), (3, 7), (0, 7)],
        [(0, 0), (8, 0), (8, 8), (6, 8), (6, 3), (2, 3), (2, 8), (0, 8)],
        [(0, 0), (9, 0), (5, 7)],
        [(0, 3), (3, 0), (6, 3), (3, 6)],
        [(0, 0), (3, 0), (8, 0), (8, 6), (0, 6)],
    ]
    counts = {"winding_comparisons": 0, "source_promise_comparisons": 0,
              "boundary_comparisons": 0, "analytic_histogram_comparisons": 0,
              "metamorphic_comparisons": 0, "invalid_input_rejections": 0}
    for poly in fixtures:
        for x in range(-2, 12):
            for y in range(-2, 12):
                p = (x, y)
                actual = point_in_polygon(poly, p)
                expected = winding_oracle(poly, p)
                assert actual == expected, (poly, p, actual, expected)
                counts["winding_comparisons"] += 1
                counts["source_promise_comparisons"] += not on_supporting_line(poly, p)
                counts["boundary_comparisons"] += expected == "boundary"
                for shift, scale in [((0, 0), -1), ((17, -31), 3), ((10**80, -(10**90)), 10**60)]:
                    transformed = [(xx * scale + shift[0], yy * scale + shift[1]) for xx, yy in reversed(poly)]
                    query = (x * scale + shift[0], y * scale + shift[1])
                    assert point_in_polygon(transformed, query) == expected
                    counts["metamorphic_comparisons"] += 1
    rng = random.Random(87022)
    for _ in range(120):
        heights = [rng.randint(1, 9) for _ in range(rng.randint(2, 10))]
        # Scale by 2 so odd test coordinates lie strictly within each column.
        poly = [(2 * x, 2 * y) for x, y in histogram(heights)]
        for x in range(-1, 2 * len(heights) + 2):
            for y in range(-1, 21):
                p = (x, y)
                actual = point_in_polygon(poly, p)
                assert actual == winding_oracle(poly, p)
                counts["winding_comparisons"] += 1
                counts["source_promise_comparisons"] += not on_supporting_line(poly, p)
                if x % 2 == 1 and y % 2 == 1:
                    expected = (0 < x < 2 * len(heights) and 0 < y < 2 * heights[x // 2])
                    assert actual == ("inside" if expected else "outside")
                    counts["analytic_histogram_comparisons"] += 1
    # These violate only cheap input-shape checks, not the unvalidated simplicity promise.
    for poly, p in [([], (0, 0)), ([(0, 0), (1, 1)], (2, 2)),
                    ([(0, 0), (0, 0), (2, 1)], (3, 3)),
                    ([(0, 0), (2, 0), (0, 2)], (0.5, 1)),
                    ([(0, 0), (2.0, 0), (0, 2)], (3, 3))]:
        try:
            point_in_polygon(poly, p)
        except ValueError:
            counts["invalid_input_rejections"] += 1
        else:
            raise AssertionError((poly, p))
    result = {"question_id": "PREP-087", "passed": True, "seed": 87022,
              "checks": counts, "fixed_fixtures": len(fixtures), "random_simple_histograms": 120,
              "scope": "Exact integer simple polygons; independent signed-winding and analytic histogram oracles. Reversed orientation, reflection, translation and huge integers. Boundary helper tested separately. No simplicity validator or self-intersection fill-rule claim."}
    (ROOT / "checks/prep-087-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
