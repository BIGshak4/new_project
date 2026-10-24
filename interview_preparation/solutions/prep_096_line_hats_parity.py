"""PREP-096: a local reply uses only visible hats and previously heard answers.

Colors: white=0, black=1. The first answer is a parity message, not a
reliably decoded hat. The simulation knows the world only to present each
prisoner with permitted observations; reply() never receives their own hat.
"""
from collections.abc import Sequence


def reply(visible: Sequence[int], heard: Sequence[int]) -> int:
    parity = 0
    for color in visible:
        parity ^= color
    for answer in heard:
        parity ^= answer
    return parity


def simulate(hats_front_to_back: Sequence[int]) -> list[int]:
    if not hats_front_to_back or any(color not in (0, 1) for color in hats_front_to_back):
        raise ValueError('A positive number of binary-color hats is required')
    heard: list[int] = []
    for index in range(len(hats_front_to_back) - 1, -1, -1):
        heard.append(reply(hats_front_to_back[:index], heard))
    return heard  # rear-to-front answer order
