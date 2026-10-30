"""A nondirectional sensor can have identical observations for opposite traversals."""


def single_sensor_trace(direction):
    if direction not in ("entry", "exit"):
        raise ValueError("direction required")
    return (0, 1, 0)


def two_sensor_trace(direction):
    if direction not in ("entry", "exit"):
        raise ValueError("direction required")
    return (
        ((0, 0), (1, 0), (1, 1), (0, 1), (0, 0))
        if direction == "entry"
        else ((0, 0), (0, 1), (1, 1), (1, 0), (0, 0))
    )
