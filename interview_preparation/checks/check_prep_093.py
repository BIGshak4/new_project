"""Exact areas, congruence and an independent point-membership coverage check."""
import importlib.util
import json
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("partition", ROOT / "solutions/prep_093_equal_partitions.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def inside(p, vertices):
    x, y = p
    parity = False
    for (ax, ay), (bx, by) in zip(vertices, vertices[1:] + vertices[:1]):
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            parity = not parity
    return parity


def region_oracle(x, y):
    """Read the added grid geometry directly, without using polygon outlines."""
    if (1 < x < 3 and 1 < y < 2) or (1 < x < 2 and 2 < y < 3):
        return None
    return ("B" if x < 2 else "A") if y < 2 else ("C" if x < 2 else "D")


def congruence_signature(vertices):
    # Drop collinear half-cell vertices, then normalize every square symmetry.
    vertices = list(vertices)
    changed = True
    while changed:
        changed = False
        for i, b in enumerate(vertices):
            a, c = vertices[i - 1], vertices[(i + 1) % len(vertices)]
            if (b[0] - a[0]) * (c[1] - b[1]) == (b[1] - a[1]) * (c[0] - b[0]):
                vertices.pop(i)
                changed = True
                break
    variants = []
    for swap in [False, True]:
        for sx in [-1, 1]:
            for sy in [-1, 1]:
                points = [(sx * (y if swap else x), sy * (x if swap else y)) for x, y in vertices]
                xmin, ymin = min(x for x, _ in points), min(y for _, y in points)
                variants.append(tuple(sorted((x - xmin, y - ymin) for x, y in points)))
    return min(variants)


def main():
    partitions = model.partitions()
    for region, count in [("A", 2), ("B", 3), ("C", 4), ("D", 7)]:
        pieces = partitions[region]
        total = F(4 if region == "D" else 3)
        assert len(pieces) == count
        assert all(model.polygon_area(piece) == total / count for piece in pieces)
        assert sum(model.polygon_area(piece) for piece in pieces) == total
        assert len({congruence_signature(piece) for piece in pieces}) == 1
    # All boundaries lie on integer, half-integer, diagonal x+y=4, or D's
    # sevenths grid. Each subdivision cell has constant membership, except
    # diagonal cells which are tested on both sides separately. The odd
    # asymmetric offsets avoid EVERY boundary including x+y=4.
    cases = 0
    for ix in range(224):
        for iy in range(224):
            x, y = F(ix, 56) + F(1, 224), F(iy, 56) + F(1, 448)
            expected = region_oracle(x, y)
            hits = [r for r, pieces in partitions.items() for piece in pieces if inside((x, y), piece)]
            assert hits == ([] if expected is None else [expected]), (x, y, hits, expected)
            cases += 1
    assert sum(model.polygon_area(p) for ps in partitions.values() for p in ps) == 13
    evidence = {
        "question_id": "PREP-093", "status": "passed",
        "piece_counts": {k: len(v) for k, v in partitions.items()},
        "exact_piece_areas": {k: str(model.polygon_area(v[0])) for k, v in partitions.items()},
        "congruence": "All pieces within each region have identical polygon vertex sets under translation and a square symmetry, after removing collinear vertices.",
        "independent_point_membership_cases": cases,
        "total_white_area": 13,
        "scope": "Exact added 4x4 ideal grid, not dimensions measured from a screenshot; finite grid coverage is an additional check, not a general polygon theorem.",
    }
    (ROOT / "checks/prep-093-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()
