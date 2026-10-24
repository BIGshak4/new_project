"""Independent finite worlds and exact arithmetic for 18 reasoning study cards.

These do not execute an answer implementation: the cards are explanatory prose.
Tests instead construct possible histories, geometric shapes and decision trees,
including counterexamples to the tempting but incorrect answers.
"""

from __future__ import annotations

import itertools
import json
import math
from fractions import Fraction
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps/web/src/content"
CARDS = json.loads((CONTENT / "fundamentals-reasoning-250.json").read_text("utf-8"))
BY_ID = {card["id"]: card for card in CARDS}


def assert_claim(number: int, token: str) -> None:
    """Keep the computed result attached to both actual learner-facing answers."""
    for language in ("he", "en"):
        assert token in BY_ID[f"quick-sw-{number}"]["answer"][language]


def test_authored_cards_contract_localization_and_traceable_interview_basis():
    assert list(BY_ID) == [f"quick-sw-{number}" for number in range(101, 119)]
    assert len(CARDS) == len(BY_ID) == 18
    interview_ids = {
        question["id"]
        for question in json.loads(
            (ROOT / "interview_preparation/questions.json").read_text("utf-8")
        )["questions"]
    }
    old = []
    for name in (
        "fundamentals-code-logic.json", "fundamentals-code-expansion.json",
        "fundamentals-hardware.json", "fundamentals-hardware-expansion.json",
        "fundamentals-reasoning-expansion.json",
    ):
        old.extend(json.loads((CONTENT / name).read_text("utf-8")))
    assert set(BY_ID).isdisjoint(card["id"] for card in old)
    for card in CARDS:
        assert card["topic"] == "reasoning"
        assert set(card) == {
            "id", "topic", "interviewIds", "title", "prompt", "answer", "takeaway",
        }
        assert card["interviewIds"]
        assert set(card["interviewIds"]) <= interview_ids
    for field, limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
        for language in ("he", "en"):
            values = [card[field][language] for card in CARDS]
            assert len(set(values)) == len(values)
            assert set(values).isdisjoint(card[field][language] for card in old)
            for card, value in zip(CARDS, values, strict=True):
                assert set(card[field]) == {"he", "en"}
                assert value.strip() and len(value.split()) <= limit
                assert "\ufffd" not in value
                if language == "he":
                    assert any("\u0590" <= char <= "\u05ff" for char in value)


def test_101_unknown_initial_signal_can_add_only_one_phantom_count():
    states = list(itertools.product(range(3), repeat=3))
    for sent in states:
        for initial_count in (0, 1):
            count = sum(sent) + initial_count
            if count >= 6:
                assert all(value > 0 for value in sent)
            if 0 in sent:
                assert count <= 5
    # A threshold of five would be wrong: an absent reporter is still possible.
    assert sum((2, 2, 0)) + 1 == 5
    assert sum((2, 2, 2)) == 6
    # General bound with r reporters, quota q and an initial offset <= b.
    for reporters, quota, offset in itertools.product(range(2, 6), range(1, 4), range(3)):
        no_one_missing_threshold = (reporters - 1) * quota + offset + 1
        for contributions in itertools.product(range(quota + 1), repeat=reporters):
            if 0 in contributions:
                assert sum(contributions) + offset < no_one_missing_threshold
    assert_claim(101, "2×2=4")
    assert_claim(101, "5")


def test_102_dummy_toggle_preserves_uncollected_message_for_every_visitor_prefix():
    for initial_dummy in (0, 1):
        for visitors in range(9):
            signal, dummy, collected = 1, initial_dummy, 0
            for _ in range(visitors):
                dummy = 1 - dummy
                assert signal == 1 and collected == 0
            assert dummy == initial_dummy ^ (visitors % 2)
            # The authorized collector performs one toggle and one collection.
            before = (signal, dummy)
            signal = 0
            collected += 1
            assert sum(a != b for a, b in zip(before, (signal, dummy), strict=True)) == 1
            assert collected == 1
    # Mandatory toggles on the signal itself would erase an unread message.
    assert 1 - 1 == 0


def test_103_first_success_histories_give_first_player_two_thirds():
    # Enumerate mutually exclusive histories: A wins on toss 1,3,5,...;
    # B wins on 2,4,6,...; the remaining mass is the all-fail prefix.
    expected_a, expected_b = Fraction(2, 3), Fraction(1, 3)
    for rounds in range(1, 17):
        wins_a = sum(Fraction(1, 2 ** (2 * r + 1)) for r in range(rounds))
        wins_b = sum(Fraction(1, 2 ** (2 * r + 2)) for r in range(rounds))
        all_fail = Fraction(1, 4**rounds)
        assert wins_a + wins_b + all_fail == 1
        # Residual histories restart with unchanged turn and probabilities.
        assert wins_a + all_fail * expected_a == expected_a
        assert wins_b + all_fail * expected_b == expected_b
        assert wins_a > wins_b
    assert_claim(103, "2/3")
    assert_claim(103, "1/3")


def test_104_joint_success_uses_conditional_not_independent_probability():
    worlds = set(itertools.product(range(5), range(2)))
    reaches = {world for world in worlds if world[0] < 3}
    wins = {world for world in reaches if world[1] == 0}
    p_reaches = Fraction(len(reaches), len(worlds))
    p_wins_given_reaches = Fraction(len(wins & reaches), len(reaches))
    p_wins = Fraction(len(wins), len(worlds))
    assert (p_reaches, p_wins_given_reaches, p_wins) == (
        Fraction(3, 5), Fraction(1, 2), Fraction(3, 10),
    )
    assert p_wins == p_reaches * p_wins_given_reaches
    # Winning implies reaching, so these events are explicitly not independent.
    assert Fraction(len(wins & reaches), len(worlds)) != p_wins * p_reaches
    assert_claim(104, "3/10")


def test_105_piecewise_motion_equal_endpoint_speed_does_not_fix_arrival_time():
    trips = (((1, 1), (1, 2)), ((2, 2),))  # (segment length, segment speed)
    assert [sum(length for length, _ in trip) for trip in trips] == [2, 2]
    assert [trip[-1][1] for trip in trips] == [2, 2]
    durations = [sum(Fraction(length, speed) for length, speed in trip) for trip in trips]
    assert durations == [Fraction(3, 2), Fraction(1)]
    # Subdividing a constant-speed segment cannot change its duration.
    for pieces in range(1, 21):
        assert sum(Fraction(2, pieces) / 2 for _ in range(pieces)) == durations[1]
    assert_claim(105, "1.5")


def test_106_energy_balance_is_independent_of_positive_point_mass():
    gravitational_acceleration, descent = 10, 5
    for mass in (Fraction(1, 100), Fraction(1, 3), Fraction(1), Fraction(7), Fraction(100)):
        energy_lost = mass * gravitational_acceleration * descent
        possible_speeds = [
            speed for speed in range(21)
            if mass * speed * speed / 2 == energy_lost
        ]
        assert possible_speeds == [10]
        assert mass * 100 / 2 == energy_lost
    assert_claim(106, "10")
    assert_claim(106, "v²=100")


def test_107_static_moment_balance_matches_center_of_mass():
    # Independent mass-weighted position and force moments agree.
    masses_and_positions = ((2, -1), (1, 2))
    total_mass = sum(mass for mass, _ in masses_and_positions)
    centre = Fraction(sum(mass * x for mass, x in masses_and_positions), total_mass)
    assert centre == 0
    for gravity in (Fraction(1, 2), Fraction(98, 10), Fraction(10)):
        signed_moment = sum(mass * gravity * x for mass, x in masses_and_positions)
        assert signed_moment == 0
        # Moving the light weight inward breaks the balance despite same masses.
        assert 2 * gravity * -1 + gravity * 1 != 0


def test_108_planar_moments_need_both_components():
    positions = ((-1, 1), (1, 1))
    assert sum(x for x, _ in positions) == 0
    assert sum(y for _, y in positions) == 2
    # r cross F for r=(x,y,0), F=(0,0,-1): torque=(-y,x,0).
    torques = [(-y, x, 0) for x, y in positions]
    total = tuple(sum(moment[axis] for moment in torques) for axis in range(3))
    assert total == (-2, 0, 0)
    assert total != (0, 0, 0)
    assert_claim(108, "(0,0)")


def test_109_superposition_preserves_zero_added_moment():
    # Exact lattice triples, independently characterized by centre of mass.
    points = list(itertools.product(range(-2, 3), repeat=2))
    balanced_triples = [
        triple for triple in itertools.combinations(points, 3)
        if all(sum(point[axis] for point in triple) == 0 for axis in range(2))
    ]
    assert balanced_triples
    for triple in balanced_triples:
        for x, y in points:
            arrangement = (*triple, (x, y), (-x, -y))
            # Check physical vertical-force moments, not just cardinality.
            assert sum(-point[1] for point in arrangement) == 0
            assert sum(point[0] for point in arrangement) == 0
    assert_claim(109, "0+0=0")


def test_110_zero_first_derivative_at_upper_equilibrium_is_not_stability():
    # A mass at distance r above a fixed pivot has height r*cos(theta).
    # Any nonzero sufficiently small tilt lowers energy and creates outward torque.
    for radius, angle in itertools.product((Fraction(1, 4), 1, 3), (0.001, 0.01, 0.1)):
        upright_height = float(radius)
        tilted_height = float(radius) * math.cos(angle)
        assert tilted_height < upright_height
        assert math.sin(angle) > 0  # Gravity drives an already-positive tilt outward.
        assert math.cos(-angle) == math.cos(angle)
    assert math.sin(0) == 0


U_POLYGON = ((0, 0), (6, 0), (6, 6), (4, 6), (4, 2), (2, 2), (2, 6), (0, 6))


def right_ray_crossings(polygon, point):
    """Exact intersection coordinates; no division-free card algorithm is reused."""
    px, py = point
    crossings = []
    for a, b in zip(polygon, (*polygon[1:], polygon[0]), strict=True):
        if (a[1] > py) == (b[1] > py):
            continue
        x_intersection = a[0] + Fraction(py - a[1], b[1] - a[1]) * (b[0] - a[0])
        if x_intersection > px:
            crossings.append(x_intersection)
    return crossings


def test_111_concave_polygon_has_multiple_interior_intervals():
    assert right_ray_crossings(U_POLYGON, (1, 4)) == [6, 4, 2]
    assert right_ray_crossings(U_POLYGON, (3, 4)) == [6, 4]
    # Independent analytic union of three rectangles gives the inside oracle.
    for x, y in itertools.product(range(-1, 14), repeat=2):
        px, py = Fraction(x, 2) + Fraction(1, 7), Fraction(y, 2) + Fraction(1, 7)
        inside_union = (
            0 < px < 6 and 0 < py < 2
            or 0 < px < 2 and 0 < py < 6
            or 4 < px < 6 and 0 < py < 6
        )
        assert bool(len(right_ray_crossings(U_POLYGON, (px, py))) % 2) == inside_union


def test_112_half_open_vertices_agree_with_neighboring_nondegenerate_rays():
    # Shared vertex at (2,0), one neighbor below and one above.
    below, vertex, above = (1, -1), (2, 0), (3, 1)
    edges = ((below, vertex), (vertex, above))
    naive_closed = sum(min(a[1], b[1]) <= 0 <= max(a[1], b[1]) for a, b in edges)
    correct_half_open = sum((a[1] > 0) != (b[1] > 0) for a, b in edges)
    assert naive_closed == 2 and correct_half_open == 1
    for level in (-Fraction(1, 100), Fraction(1, 100)):
        proper = sum(min(a[1], b[1]) < level < max(a[1], b[1]) for a, b in edges)
        assert proper == 1
    # A touch at a local extremum changes the crossing count by an even number.
    for neighbor_height in (-1, 1):
        touch_edges = (((1, neighbor_height), vertex), (vertex, (3, neighbor_height)))
        counted = sum((a[1] > 0) != (b[1] > 0) for a, b in touch_edges)
        assert counted in (0, 2)
    assert_claim(112, "(Ay>Py)!=(By>Py)")


def test_113_even_odd_and_winding_intentionally_disagree_on_double_traversal():
    square = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    for turns in range(1, 5):
        walk = square * turns
        intersections = right_ray_crossings(walk, (0, 0))
        assert len(intersections) == turns
        # Independent winding: sum signed angle changes around the point.
        angles = []
        for a, b in zip(walk, (*walk[1:], walk[0]), strict=True):
            cross, dot = a[0] * b[1] - a[1] * b[0], a[0] * b[0] + a[1] * b[1]
            angles.append(math.atan2(cross, dot))
        winding = round(sum(angles) / (2 * math.pi))
        assert winding == turns
        if turns == 2:
            assert len(intersections) % 2 == 0 and winding != 0


def test_114_circumference_difference_cancels_every_original_radius():
    # Store exact coefficients of pi, avoiding approximate cancellation at Earth scale.
    extra_circumference_coefficient = Fraction(2)
    for radius in (Fraction(1, 100), Fraction(7), Fraction(1000), Fraction(10**30)):
        original_coefficient = 2 * radius
        enlarged_coefficient = original_coefficient + extra_circumference_coefficient
        enlarged_radius = enlarged_coefficient / 2
        assert enlarged_radius - radius == 1
    assert_claim(114, "2π(R+h)−2πR=2πh")
    assert_claim(114, "h=1")


def test_115_path_speed_order_can_reverse_angular_speed_order():
    swimmer_speed, swimmer_radius = Fraction(1), Fraction(1, 4)
    runner_speed, runner_radius = Fraction(3), Fraction(1)
    assert swimmer_speed < runner_speed
    swimmer_rate = swimmer_speed / swimmer_radius
    runner_rate = runner_speed / runner_radius
    assert (swimmer_rate, runner_rate) == (4, 3)
    assert swimmer_rate > runner_rate
    # Independent time to traverse a one-radian arc equals arc length / speed.
    swimmer_time = swimmer_radius / swimmer_speed
    runner_time = runner_radius / runner_speed
    assert swimmer_time == Fraction(1, 4) < runner_time == Fraction(1, 3)
    assert_claim(115, "=4")
    assert_claim(115, "=3")


def test_116_equal_area_rectangles_are_not_congruent_under_rigid_isometries():
    rectangle = ((0, 0), (1, 0), (1, 4), (0, 4))
    square = ((0, 0), (2, 0), (2, 2), (0, 2))

    def twice_area(vertices):
        return abs(sum(
            a[0] * b[1] - b[0] * a[1]
            for a, b in zip(vertices, (*vertices[1:], vertices[0]), strict=True)
        ))

    def squared_pair_distances(vertices):
        return sorted(
            (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
            for a, b in itertools.combinations(vertices, 2)
        )

    assert twice_area(rectangle) == twice_area(square) == 8
    # Every rigid isometry preserves all pairwise distances, regardless of relabeling.
    assert squared_pair_distances(rectangle) == [1, 1, 16, 16, 17, 17]
    assert squared_pair_distances(square) == [4, 4, 4, 4, 8, 8]
    assert squared_pair_distances(rectangle) != squared_pair_distances(square)


def test_117_exhaustive_minimax_threshold_worlds_respect_lost_ball_resource():
    # Thresholds 1..N+1 include the no-breaking-floor case N+1.
    @cache
    def solvable(thresholds: tuple[int, ...], balls: int, drops: int) -> bool:
        if len(thresholds) <= 1:
            return True
        if balls == 0 or drops == 0:
            return False
        for floor in range(thresholds[0], thresholds[-1]):
            breaks = tuple(value for value in thresholds if value <= floor)
            survives = tuple(value for value in thresholds if value > floor)
            if solvable(breaks, balls - 1, drops - 1) and solvable(survives, balls, drops - 1):
                return True
        return False

    assert solvable(tuple(range(1, 8)), 2, 3)
    assert not solvable(tuple(range(1, 9)), 2, 3)
    assert solvable(tuple(range(1, 4)), 1, 2)
    assert not solvable(tuple(range(1, 5)), 1, 2)
    assert solvable(tuple(range(1, 5)), 2, 2)
    assert not solvable(tuple(range(1, 6)), 2, 2)
    # Actual strategy covering every threshold in six floors in <=3 drops.
    for actual_threshold in range(1, 8):
        possible, balls, drops = set(range(1, 8)), 2, 0
        plan = [3]
        while len(possible) > 1:
            floor = plan.pop(0)
            breaks = floor >= actual_threshold
            possible = {f for f in possible if (f <= floor) == breaks}
            balls -= int(breaks)
            drops += 1
            if drops == 1:
                plan = [1, 2] if breaks else [5]
            elif drops == 2 and floor == 5:
                plan = [4] if breaks else [6]
            assert balls >= 0 and drops <= 3
        assert possible == {actual_threshold}
    assert_claim(117, "2+1+3=6")


def test_118_parity_message_does_not_reveal_first_speakers_invisible_hat():
    for visible_count in range(7):
        for visible in itertools.product((0, 1), repeat=visible_count):
            # Black=1, white=0. The first response deliberately encodes others.
            reply = sum(visible) % 2
            indistinguishable_worlds = [(own, visible, reply) for own in (0, 1)]
            assert len({world[2] for world in indistinguishable_worlds}) == 1
            assert sum(world[0] == world[2] for world in indistinguishable_worlds) == 1
            if reply == 0:
                assert {world[0] for world in indistinguishable_worlds} == {0, 1}
    # Concrete pair: two visible black hats, while speaker may wear either color.
    assert sum((1, 1)) % 2 == 0
