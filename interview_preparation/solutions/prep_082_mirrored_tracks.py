"""Travel time for ideal guided point masses on mirrored semicircular features.

This model prescribes contact and conserved mechanical energy. It does not
simulate rolling, detachment, impacts, friction, or arbitrary track profiles.
"""
from math import pi, sin, sqrt


def speed(height, feature_height, gravity=9.81):
    if gravity <= 0 or height <= feature_height:
        raise ValueError("Positive gravity and positive remaining energy required")
    return sqrt(2 * gravity * (height - feature_height))


def feature_time(height, radius, *, dip=False, gravity=9.81, intervals=4096):
    """Simpson quadrature; height>radius ensures the hill can be traversed."""
    if radius <= 0 or height <= radius or gravity <= 0:
        raise ValueError("Require H>R2>0 and g>0")
    if not isinstance(intervals, int) or intervals < 2 or intervals % 2:
        raise ValueError("An even positive interval count is required")
    step = pi / intervals
    sign = -1 if dip else 1

    def integrand(theta):
        return radius / speed(height, sign * radius * sin(theta), gravity)

    total = integrand(0) + integrand(pi)
    total += sum((4 if i % 2 else 2) * integrand(i * step) for i in range(1, intervals))
    return total * step / 3


if __name__ == "__main__":
    for dip in (False, True):
        print("dip" if dip else "hill", feature_time(3.0, 1.0, dip=dip))
