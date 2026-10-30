"""Conditional inference: a known final side anchors crossing parity."""


def infer_initial_inside(crossing_events, *, final_inside=None):
    if type(final_inside) is not bool:
        raise ValueError("A known final inside/outside anchor is required")
    parity = False
    for crossed in crossing_events:
        if type(crossed) is not bool:
            raise ValueError("Each event must report a genuine crossing as a bool")
        parity ^= crossed
    return final_inside ^ parity


def from_outside_coast(crossing_events):
    """Valid only if the reached coast is known outside the closed fence."""
    return infer_initial_inside(crossing_events, final_inside=False)
