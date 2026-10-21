"""Exact-target 21 game: start at zero, add 1/2/3, first to 21 wins.

Moves past 21 are forbidden. The returned move is winning only when the
current position admits a forced win; None means terminal or losing position.
"""


def winning_move(total: int) -> int | None:
    if type(total) is not int or not 0 <= total <= 21:
        raise ValueError("total must be an integer in 0..21")
    remaining = 21 - total
    move = remaining % 4
    return move if move else None


def complement_reply(opponent_move: int) -> int:
    """Use after first choosing 1, while maintaining 1,5,9,13,17,21."""
    if type(opponent_move) is not int or opponent_move not in (1, 2, 3):
        raise ValueError("opponent_move must be 1, 2 or 3")
    return 4 - opponent_move
