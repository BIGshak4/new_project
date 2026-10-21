"""Exact finite-state analysis of the abstract three-player elimination game.

Policies select a different player or None (deliberate miss). Two remaining
players always attempt to eliminate the opponent. Turns cycle A,B,C, skipping
eliminated participants. Positive independent success probabilities are fixed.
"""

from fractions import Fraction
from itertools import product

PLAYERS = ("A", "B", "C")
ACCURACY = {"A": Fraction(1, 10), "B": Fraction(1, 2), "C": Fraction(9, 10)}
PROPOSED_POLICY = {"A": None, "B": "C", "C": "B"}


def next_alive(current: str, alive: set[str]) -> str:
    position = PLAYERS.index(current)
    for offset in (1, 2, 3):
        candidate = PLAYERS[(position + offset) % 3]
        if candidate in alive:
            return candidate
    raise ValueError("empty alive set")


def duel_win(winner: str, opponent: str, first: str) -> Fraction:
    p, q = ACCURACY[winner], ACCURACY[opponent]
    denominator = p + q - p * q
    return p / denominator if first == winner else (1 - q) * p / denominator


def hit_distribution(actor: str, target: str) -> dict[str, Fraction]:
    alive = set(PLAYERS) - {target}
    first = next_alive(actor, alive)
    opponent = next(player for player in alive if player != actor)
    own = duel_win(actor, opponent, first)
    return {player: own if player == actor else 1 - own if player == opponent else Fraction(0)
            for player in PLAYERS}


def evaluate_policy(policy: dict[str, str | None]) -> dict[str, dict[str, Fraction]]:
    """Return each winner's probabilities indexed by next all-alive turn.

    Solve the cyclic first-step recurrence algebraically; an all-miss policy
    never absorbs and is explicitly rejected rather than assigned win values.
    """
    continuation, reward = {}, {}
    for actor in PLAYERS:
        target = policy[actor]
        if target is not None and target not in set(PLAYERS) - {actor}:
            raise ValueError("target must be an opponent or None")
        continuation[actor] = Fraction(1) if target is None else 1 - ACCURACY[actor]
        reward[actor] = {player: Fraction(0) for player in PLAYERS} if target is None else {
            player: ACCURACY[actor] * value for player, value in hit_distribution(actor, target).items()
        }
    denominator = 1 - continuation["A"] * continuation["B"] * continuation["C"]
    if denominator == 0:
        raise ValueError("all-miss policy never terminates")
    values = {}
    for index, first in enumerate(PLAYERS):
        second, third = PLAYERS[(index + 1) % 3], PLAYERS[(index + 2) % 3]
        values[first] = {
            winner: (reward[first][winner] + continuation[first] * reward[second][winner]
                     + continuation[first] * continuation[second] * reward[third][winner]) / denominator
            for winner in PLAYERS
        }
    return values


def one_step_value(actor: str, target: str | None, values) -> Fraction:
    """Act once, then return to the evaluated policy at every later state."""
    following = next_alive(actor, set(PLAYERS))
    if target is None:
        return values[following][actor]
    return (ACCURACY[actor] * hit_distribution(actor, target)[actor]
            + (1 - ACCURACY[actor]) * values[following][actor])


def stationary_equilibria():
    """Enumerate deterministic stationary policies under the specified model."""
    choices = [[None] + [other for other in PLAYERS if other != actor] for actor in PLAYERS]
    equilibria = []
    for actions in product(*choices):
        policy = dict(zip(PLAYERS, actions))
        try:
            values = evaluate_policy(policy)
        except ValueError:
            continue
        if all(one_step_value(actor, target, values) <= values[actor][actor]
               for actor, options in zip(PLAYERS, choices) for target in options):
            equilibria.append(policy)
    return equilibria
