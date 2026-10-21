"""PREP-063: rigorous sufficient escape strategy, not an optimality solver.

The fox remains on the shore at speed <=4v. The duck swims at <=v, starts at
the center (or first reaches it from a safe interior point), and observes the
fox continuously. Units may be normalized to R=v=1 without changing ratios.
"""
from math import pi

ORBIT_FRACTION = 6 / 25


def strategy_bounds(radius=1.0, duck_speed=1.0):
    if radius <= 0 or duck_speed <= 0:
        raise ValueError("Require positive radius and duck speed")
    r = radius * ORBIT_FRACTION
    fox_speed = 4 * duck_speed
    duck_angular = duck_speed / r
    fox_angular = fox_speed / radius
    advantage = duck_angular - fox_angular
    return {
        "orbit_radius": r,
        "duck_angular_speed": duck_angular,
        "fox_max_angular_speed": fox_angular,
        "angular_advantage": advantage,
        "center_to_orbit_time": r / duck_speed,
        "alignment_time_upper_bound": pi / advantage,
        "radial_sprint_time": (radius - r) / duck_speed,
        "fox_earliest_endpoint_time": pi * radius / fox_speed,
        "strict_time_margin": pi * radius / fox_speed - (radius - r) / duck_speed,
    }


def orbit_direction(initial_signed_gap):
    """Gap is duck angle minus fox angle, represented in [-pi, pi]."""
    if not -pi <= initial_signed_gap <= pi:
        raise ValueError("Principal angular gap required")
    return 1 if initial_signed_gap >= 0 else -1


def alignment_time(initial_signed_gap, fox_angular_velocity, radius=1.0, duck_speed=1.0):
    """Exact for constant fox angular velocity, bounded in absolute value.

    The proof in the text also covers arbitrary bounded time-varying policies;
    this helper does not pretend a constant-velocity test is that full proof.
    """
    bounds = strategy_bounds(radius, duck_speed)
    limit = bounds["fox_max_angular_speed"]
    if abs(fox_angular_velocity) > limit + 1e-12:
        raise ValueError("Fox exceeds its speed bound")
    direction = orbit_direction(initial_signed_gap)
    remaining = pi - abs(initial_signed_gap)
    progress_speed = bounds["duck_angular_speed"] - direction * fox_angular_velocity
    return remaining / progress_speed


if __name__ == "__main__":
    for name, value in strategy_bounds().items():
        print(f"{name}: {value:.9f}")
