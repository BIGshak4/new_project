"""Replies receive only visible hats and earlier audible answers.

Color codes red=0, blue=1, third=2. Lists run front to rear. Speakers answer
rear to front. The simulator alone knows each speaker's true hat.
"""


def pair_reply(visible, heard):
    if len(heard) % 2 == 0:
        return visible[-1] if visible else 0
    return heard[-1]


def two_parities_reply(visible, heard):
    if not heard:
        # Exclude the second signaler, nearest in front of the first.
        return sum(color == 0 for color in visible[:-1]) % 2
    if len(heard) == 1:
        return sum(color == 1 for color in visible) % 2
    known = list(visible) + list(heard[2:])
    red = (heard[0] - sum(color == 0 for color in known)) % 2
    blue = (heard[1] - sum(color == 1 for color in known)) % 2
    return {(1, 0): 0, (0, 1): 1, (0, 0): 2}[red, blue]


def modulo_three_reply(visible, heard):
    if not heard:
        return sum(visible) % 3
    return (heard[0] - sum(visible) - sum(heard[1:])) % 3


def simulate(hats, strategy):
    hats = tuple(hats)
    if not hats or any(type(x) is not int or not 0 <= x < 3 for x in hats):
        raise ValueError("nonempty line of three-color hats required")
    if strategy == "two_parities" and len(hats) < 2:
        raise ValueError("two signalers require at least two people")
    methods = {"pairs": pair_reply, "two_parities": two_parities_reply, "modulo_three": modulo_three_reply}
    if strategy not in methods:
        raise ValueError("unknown strategy")
    heard, correct = [], []
    for index in range(len(hats) - 1, -1, -1):
        answer = methods[strategy](hats[:index], tuple(heard))
        heard.append(answer)
        correct.append(answer == hats[index])
    return tuple(heard), tuple(correct)
