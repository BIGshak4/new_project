"""Settled water-displacement balance for an inert unforced object."""

from fractions import Fraction


def displacement_change(mass, object_volume, water_density, pool_area=1):
    mass, volume, density, area = map(
        Fraction, (mass, object_volume, water_density, pool_area)
    )
    if min(mass, volume, density, area) <= 0:
        raise ValueError("positive mass, volume, water density and pool area required")
    before = mass / density  # Additional displacement while carried by the boat.
    object_density = mass / volume
    state = (
        "sinks"
        if object_density > density
        else "floats"
        if object_density < density
        else "neutral"
    )
    after = volume if state == "sinks" else mass / density
    return {
        "object_density": object_density,
        "state": state,
        "before": before,
        "after": after,
        "volume_change": after - before,
        "level_change": (after - before) / area,
    }
