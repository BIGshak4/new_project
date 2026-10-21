"""Independent absorbing-chain equations, Gaussian elimination and deviations."""

import json
from fractions import Fraction as F
from importlib.util import module_from_spec, spec_from_file_location
from itertools import combinations, product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("game", BANK / "solutions/prep_079_cyclic_probability_game.py")
solution = module_from_spec(spec)
spec.loader.exec_module(solution)
NAMES = ("A", "B", "C")
HITS = {"A": F(1, 10), "B": F(1, 2), "C": F(9, 10)}


def advance(turn, alive):
    index = NAMES.index(turn)
    return next(NAMES[(index + delta) % 3] for delta in (1, 2, 3)
                if NAMES[(index + delta) % 3] in alive)


def gaussian(matrix, rhs):
    rows = [list(row) + [value] for row, value in zip(matrix, rhs)]
    size = len(rows)
    for column in range(size):
        pivot = next((row for row in range(column, size) if rows[row][column]), None)
        if pivot is None:
            raise ValueError("nonabsorbing policy")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        scale = rows[column][column]
        rows[column] = [value / scale for value in rows[column]]
        for row in range(size):
            if row == column:
                continue
            scale = rows[row][column]
            rows[row] = [left - scale * right for left, right in zip(rows[row], rows[column])]
    return [row[-1] for row in rows]


def independent_chain(policy):
    states = [(frozenset(alive), turn) for size in (2, 3)
              for alive in combinations(NAMES, size) for turn in alive]
    lookup = {state: index for index, state in enumerate(states)}
    matrix = [[F(int(i == j)) for j in range(len(states))] for i in range(len(states))]
    absorption = {name: [F(0) for _ in states] for name in NAMES}
    for row, (alive, turn) in enumerate(states):
        target = next(name for name in alive if name != turn) if len(alive) == 2 else policy[turn]
        outcomes = [(F(1), alive)] if target is None else [
            (1 - HITS[turn], alive), (HITS[turn], alive - {target})]
        for probability, remaining in outcomes:
            if len(remaining) == 1:
                absorption[next(iter(remaining))][row] += probability
            else:
                destination = lookup[(frozenset(remaining), advance(turn, remaining))]
                matrix[row][destination] -= probability
    values = {name: gaussian(matrix, rhs) for name, rhs in absorption.items()}
    return {state: {name: values[name][index] for name in NAMES}
            for state, index in lookup.items()}


def run():
    checked = deviations = duel_states = 0
    choices = [[None] + [target for target in NAMES if target != actor] for actor in NAMES]
    for actions in product(*choices):
        policy = dict(zip(NAMES, actions))
        if all(action is None for action in actions):
            try:
                solution.evaluate_policy(policy)
            except ValueError:
                continue
            raise AssertionError("all-miss policy should be rejected")
        expected = independent_chain(policy)
        actual = solution.evaluate_policy(policy)
        for turn in NAMES:
            assert actual[turn] == expected[(frozenset(NAMES), turn)]
            assert sum(actual[turn].values()) == 1
            assert all(0 <= value <= 1 for value in actual[turn].values())
        checked += 1
    policy = solution.PROPOSED_POLICY
    values = solution.evaluate_policy(policy)
    one_step = {}
    for actor, options in zip(NAMES, choices):
        one_step[actor] = {}
        for target in options:
            value = solution.one_step_value(actor, target, values)
            assert value <= values[actor][actor]
            one_step[actor][target or "miss"] = str(value)
            deviations += 1
    for first, opponent in ((a, b) for a in NAMES for b in NAMES if a != b):
        p, q = HITS[first], HITS[opponent]
        shoot = solution.duel_win(first, opponent, first)
        miss = solution.duel_win(first, opponent, opponent)
        assert shoot == p + (1 - p) * miss
        assert miss == (1 - q) * shoot
        assert shoot > miss
        duel_states += 1
    equilibria = solution.stationary_equilibria()
    assert equilibria == [policy]
    assert values["A"]["A"] == F(2810, 19019)
    assert solution.one_step_value("A", "C", values) == F(27019, 190190)
    assert solution.one_step_value("A", "B", values) == F(25499, 190190)
    result = {
        "question_id": "PREP-079", "checked_on": "2026-10-21", "status": "passed_exact_probability_models",
        "absorbing_stationary_policies": checked, "transient_states_per_policy": 9,
        "equilibrium_one_step_actions": deviations, "duel_turn_states": duel_states,
        "deterministic_stationary_equilibria": equilibria,
        "first_A_actions": one_step["A"], "all_equilibrium_action_values": one_step,
        "weak_player_survival_fraction": str(values["A"]["A"]),
        "weak_player_survival_probability": float(values["A"]["A"]),
        "method": "Independent nine-transient-state exact Fraction absorbing-chain linear system solved by Gaussian elimination for all 26 terminating deterministic stationary policies. Compared every player's values from each all-alive turn with the separate cyclic-recurrence implementation. Checked all nine one-step action choices at the proposed policy and six duel turn states.",
        "limits": "Abstract game with fixed cyclic turns, independent constant success rates, intentional miss and specified payoff. Enumeration covers deterministic stationary policies; no unsupported claim about all mixed/history-dependent equilibria or real-world behavior. Professional review pending."
    }
    (BANK / "checks/prep-079-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
