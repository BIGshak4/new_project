"""Finite backward induction: survival first, meat second, sequential eating.

All lions know the preferences and remaining count. One lion eating the cow
becomes the new cow; the other lions can then make the same decision. Grass
keeps a lion alive. This is a mathematical preference model, not animal biology.
"""


def cow_is_eaten(lions: int) -> bool:
    if type(lions) is not int or lions < 0:
        raise ValueError("lions must be a nonnegative integer")
    # With zero lions the cow survives. At each next size, eating is safe
    # exactly when the resulting cow survives the smaller subgame.
    smaller_cow_eaten = False
    for _ in range(lions):
        smaller_cow_eaten = not smaller_cow_eaten
    return smaller_cow_eaten


def cow_is_eaten_constant_space_formula(lions: int) -> bool:
    if type(lions) is not int or lions < 0:
        raise ValueError("lions must be a nonnegative integer")
    return lions % 2 == 1


def outcome(lions: int) -> dict:
    eaten = cow_is_eaten_constant_space_formula(lions)
    return {"lions": lions, "initial_cow_eaten": eaten,
            "first_eater_survives": True if eaten else None}
