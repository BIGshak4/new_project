"""Independent exact or geometric oracles for seven batch70 reasoning items."""

import importlib.util
import itertools
import math
import random
from fractions import Fraction
from pathlib import Path

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def load(stem):
    spec = importlib.util.spec_from_file_location(stem, BANK / "solutions" / f"prep_{stem}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_clock():
    model = load("165_clock_three_sum_regions")
    groups = model.partition_clock()
    expected = {"upper_cap": (1, 2, 11, 12), "middle": (3, 4, 9, 10), "lower_cap": (5, 6, 7, 8)}
    assert groups == expected
    assert all(sum(group) == 26 for group in groups.values())
    assert sorted(itertools.chain.from_iterable(groups.values())) == list(range(1, 13))
    checks = 0
    normal = (math.sin(math.pi / 12), math.cos(math.pi / 12))
    for degree in range(360):
        angle = degree * math.pi / 180
        ca, sa = math.cos(angle), math.sin(angle)

        def rotated(point, ca=ca, sa=sa):
            return ca * point[0] - sa * point[1], sa * point[0] + ca * point[1]

        u = rotated(normal)
        for label in range(1, 13):
            p = rotated((math.sin(label * math.pi / 6), math.cos(label * math.pi / 6)))
            projection = u[0] * p[0] + u[1] * p[1]
            assert min(abs(projection - 0.5), abs(projection + 0.5)) > 0.2
            region = "upper_cap" if projection > 0.5 else "lower_cap" if projection < -0.5 else "middle"
            assert label in expected[region]
            checks += 1
    return {
        "status": "passed",
        "regions": 3,
        "equal_sum": 26,
        "all_clock_labels_partitioned": 12,
        "rotated_dot_product_checks": checks,
        "scope": "Combinatorial partition and numerical rotation invariance; exact chord existence follows from the written angular construction, not physical rod placement.",
    }


def check_game():
    model = load("166_symmetric_coin_game")
    one_step = two_steps = 0
    grids = []
    for radius, coin, denominator in [(2, Fraction(1, 2), 2), (3, 1, 2)]:
        candidates = [
            (Fraction(x, denominator), Fraction(y, denominator)) for x in range(-6, 7) for y in range(-6, 7)
        ]
        candidates = [p for p in candidates if model.legal_center(p, [], radius, coin)]
        grids.append((radius, coin, candidates))
        initial = [model.initial_move(radius, coin)]
        for first in candidates:
            if not model.legal_center(first, initial, radius, coin):
                continue
            reply = model.reflected_response(first)
            assert model.legal_center(reply, initial + [first], radius, coin)
            after = initial + [first, reply]
            assert set(after) == {(-x, -y) for x, y in after}
            one_step += 1
            for second in candidates:
                if not model.legal_center(second, after, radius, coin):
                    continue
                mirrored = model.reflected_response(second)
                assert model.legal_center(mirrored, after + [second], radius, coin)
                two_steps += 1
    rng = random.Random(166)
    turns = 0
    for radius, coin, candidates in grids:
        for _ in range(50):
            board = [model.initial_move(radius, coin)]
            while True:
                legal = [p for p in candidates if model.legal_center(p, board, radius, coin)]
                if not legal:
                    break
                opponent = rng.choice(legal)
                response = model.reflected_response(opponent)
                assert model.legal_center(response, board + [opponent], radius, coin)
                board.extend([opponent, response])
                assert set(board) == {(-x, -y) for x, y in board}
                assert len(board) * coin * coin <= radius * radius
                turns += 1
    return {
        "status": "passed",
        "one_reply_grid_cases": one_step,
        "two_reply_grid_cases": two_steps,
        "seeded_grid_games": 100,
        "legal_reflection_pairs_in_seeded_games": turns,
        "scope": "Exact rational disk inequalities on finite test grids; grid exhaustion is NOT proof that no continuous move exists. The continuous winning guarantee is the symmetry and finite-area proof.",
    }


def check_boat():
    model = load("167_boat_object_displacement")
    cases = 0
    states = set()
    for boat, mass, rho, volume, area in itertools.product(
        (1, 10), (1, 2, 5), (1, 2, 4), (Fraction(1, 4), Fraction(1, 2), 1, 2, 4), (1, 3)
    ):
        result = model.displacement_change(mass, volume, rho, area)
        before = Fraction(boat + mass, rho)
        # Independent full-system balance: buoyancy supports the freely
        # floating object up to rho*volume; any deficit is bottom support.
        displaced_object = Fraction(mass, rho) if mass <= rho * volume else volume
        after = Fraction(boat, rho) + displaced_object
        assert result["volume_change"] == after - before <= 0
        assert result["level_change"] * area == after - before
        assert (result["level_change"] < 0) == (mass > rho * volume)
        states.add(result["state"])
        cases += 1
    assert states == {"floats", "sinks", "neutral"}
    dense = model.displacement_change(2, Fraction(1, 1000), 1000)
    assert dense["level_change"] == Fraction(-1, 1000)
    return {
        "status": "passed",
        "exact_system_mass_balance_cases": cases,
        "density_cases": sorted(states),
        "dense_example_level_change_metres": "-1/1000",
        "scope": "Rational hydrostatic displacement under stated inert-object/no-spill assumptions. No experiment, transient waves, open-ocean level measurement or dissolving/flooding object modeled.",
    }


def check_coins():
    model = load("168_nine_lighter_coins")
    cases = 0
    paths = {}
    for genuine, ratio, bad in itertools.product(
        (1, 3, 10), (Fraction(1, 10), Fraction(1, 2), Fraction(9, 10)), range(9)
    ):
        weights = [Fraction(genuine)] * 9
        weights[bad] *= ratio
        queries = []

        def weigh(left, right, weights=weights, queries=queries):
            assert len(left) == len(right) and set(left).isdisjoint(right)
            difference = sum(weights[i] for i in left) - sum(weights[i] for i in right)
            answer = (difference > 0) - (difference < 0)
            queries.append((left, right, answer))
            return answer

        assert model.find_lighter(weigh) == bad and len(queries) == 2
        assert [len(q[0]) for q in queries] == [3, 1]
        paths[tuple(q[2] for q in queries)] = bad
        cases += 1
    assert len(paths) == 9 and set(paths.values()) == set(range(9))
    return {
        "status": "passed",
        "all_lighter_positions": 9,
        "weight_ratio_cases_per_position": 9,
        "executed_two_weighing_cases": cases,
        "distinct_two_outcome_paths": 9,
        "scope": "Exact balance oracle with one known-lighter coin and equal genuine weights; no physical balance, heavier possibility or measurement noise.",
    }


def check_urns():
    model = load("169_two_urn_red_probability")
    cases = 0
    best = Fraction(-1)
    choices = []
    for red, white in itertools.product(range(51), repeat=2):
        size = red + white
        if size in (0, 100):
            continue
        urns = (("R",) * red + ("W",) * white, ("R",) * (50 - red) + ("W",) * (50 - white))
        # Independent atomic sample-space sum: each ball has its own
        # conditional mass rather than all100 balls being equiprobable.
        expected = sum(
            (Fraction(1, 2 * len(urn)) for urn in urns for color in urn if color == "R"), Fraction(0)
        )
        actual = model.red_probability(red, white)
        assert actual == expected
        assert model.red_probability(50 - red, 50 - white) == actual
        if actual > best:
            best, choices = actual, [(red, white)]
        elif actual == best:
            choices.append((red, white))
        cases += 1
    assert model.best_allocations() == (best, tuple(choices)) == (Fraction(74, 99), ((1, 0), (49, 50)))
    return {
        "status": "passed",
        "all_nonempty_urn_allocations": cases,
        "optimal_probability": "74/99",
        "symmetric_optimal_allocations": 2,
        "scope": "Complete finite allocation enumeration and independent weighted atomic outcomes, plus written global proof. Uniform urn then uniform within-urn draw, not uniform among all100 balls.",
    }


def check_bottles():
    model = load("073_five_hundred_bottles")
    cases = invalid = 0
    for count in (9, 10):
        groups = model.tasting_groups(count)
        assert len(groups) == count
        if count == 10:
            assert groups[-1] == ()
        for poisoned in range(1, 501):
            dead = tuple(poisoned in group for group in groups)
            assert model.decode(dead) == poisoned
            cases += 1
        for label in range(500, 1 << count):
            dead = tuple(bool(label & (1 << bit)) for bit in range(count))
            try:
                model.decode(dead)
            except ValueError:
                invalid += 1
            else:
                raise AssertionError("unused outcome accepted")
        assert model.decode((False,) * count) == 1
    return {
        "status": "passed",
        "single_poison_cases_over_nine_and_ten_testers": cases,
        "unused_patterns_rejected": invalid,
        "minimum_testers": 9,
        "tenth_tester_pool_empty": True,
        "scope": "One parallel abstract binary endpoint round for500 bottles; exactly-one guarantee and adequate-dose deadline assumptions. No real poison, dosing or timing experiment.",
    }


def check_hats():
    model = load("096_thousand_binary_stages")
    worlds = 0
    for n in range(1, 13):
        minimum = n
        for hats in itertools.product((0, 1), repeat=n):
            _, correct = model.simulate(hats)
            assert all(correct[1:])
            minimum = min(minimum, sum(correct))
            if n >= 3:
                _, grouped = model.simulate(hats, True)
                assert sum(grouped) >= n - len(model.group_sizes(n)) >= (2 * n + 2) // 3
            worlds += 1
        assert minimum == n - 1
    groups = model.group_sizes(1000)
    assert groups == (3,) * 332 + (4,) and sum(groups) == 1000
    worst = [0] * 1000
    start = 0
    for size in groups:
        worst[999 - start] = 1
        start += size
    assert sum(model.simulate(worst, True)[1]) == 667
    assert sum(model.simulate([0] * 999 + [1])[1]) == 999
    rng = random.Random(9601000)
    for _ in range(200):
        hats = [rng.randrange(2) for _ in range(1000)]
        assert sum(model.simulate(hats, True)[1]) >= 667
        assert all(model.simulate(hats)[1][1:])
    return {
        "status": "passed",
        "all_binary_worlds_lengths_one_through_twelve": worlds,
        "seeded_thousand_person_worlds": 200,
        "grouped_worst_case_witness": 667,
        "global_worst_case_witness": 999,
        "groups_of_three": 332,
        "final_group_size": 4,
        "scope": "Local reply functions see only visible/previously heard data and public group sizes. Complete small assignments and sampled1000-person assignments; general guarantees follow from parity proofs.",
    }


def test_clock_partition_and_rotations():
    assert check_clock()["equal_sum"] == 26


def test_center_reflection_legality():
    assert check_game()["seeded_grid_games"] == 100


def test_boat_water_displacement_by_density():
    assert len(check_boat()["density_cases"]) == 3


def test_every_known_lighter_position():
    assert check_coins()["all_lighter_positions"] == 9


def test_every_nonempty_two_urn_allocation():
    assert check_urns()["optimal_probability"] == "74/99"


def test_all_five_hundred_bottle_patterns():
    assert check_bottles()["minimum_testers"] == 9


def test_thousand_hat_staged_guarantees():
    assert check_hats()["grouped_worst_case_witness"] == 667
