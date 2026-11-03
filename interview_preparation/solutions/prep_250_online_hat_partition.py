"""Boundary choice observes earlier hats, never the entrant's own color.

People already placed remain stationary. A newcomer may stand at any gap.
Order is left-to-right: red (0), then blue (1); no communication is required.
"""


def choose_gap(visible_colors):
    """Return the gap after the last visible red; empty line uses gap zero."""
    gap = 0
    for index, color in enumerate(visible_colors):
        if color not in (0, 1):
            raise ValueError('Binary colors required')
        if color == 0:
            gap = index + 1
    return gap


def simulate_arrival(colors):
    """Test coordinator knows hats; choose_gap receives only earlier hats."""
    placed = []
    for identity, own_color in enumerate(colors):
        if own_color not in (0, 1):
            raise ValueError('Binary colors required')
        gap = choose_gap([color for _, color in placed])
        placed.insert(gap, (identity, own_color))
    return placed
