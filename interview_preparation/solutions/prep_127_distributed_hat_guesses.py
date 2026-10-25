"""Local noncommunicating hat controller with no own-color argument.

There are n players, n colors, shared labels 0..n-1 and unrestricted repeated
colors. Each sees every OTHER hat; all guesses are simultaneous color words.
"""


def guess_from_others(player, visible_colors, color_count):
    if type(color_count) is not int or color_count < 1:
        raise ValueError("positive color count required")
    if type(player) is not int or not 0 <= player < color_count:
        raise ValueError("player label outside 0..n-1")
    if len(visible_colors) != color_count - 1:
        raise ValueError("each player must see the other n-1 hats")
    residue = 0
    for color in visible_colors:
        if type(color) is not int or not 0 <= color < color_count:
            raise ValueError("visible color outside 0..n-1")
        residue = (residue + color) % color_count
    return (player - residue) % color_count


def simulate_guesses(hats):
    """Test environment supplies each controller only that player's observations."""
    n = len(hats)
    return [guess_from_others(player, hats[:player] + hats[player + 1:], n)
            for player in range(n)]
