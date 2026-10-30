"""Models and independent oracles for second October30 reasoning intake."""
import importlib.util
from pathlib import Path

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def run(name):
    spec = importlib.util.spec_from_file_location(name, BANK / "checks" / f"check_prep_{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_checks()


def test_simultaneous_discrete_pointers_can_cross_without_same_index():
    result = run("158")
    assert result["source_simultaneous_meetings"] == 0
    assert result["integer_configuration_cases"] == 11160
    assert result["continuous_intersection_position"] == "202/5"


def test_paper_plan_separates_unknown_requirements_from_synthetic_pass_decisions():
    result = run("159")
    assert result["synthetic_interval_cases"] == 85
    assert result["declared_count_cases"] == 515
    assert result["orientation_invariance_cases"] == 32


def test_blind_three_coin_plan_covers_every_thirty_coin_arrangement():
    assert run("059_thirty_coins")["all_three_black_placements"] == 4060


def test_three_color_strategies_use_only_permitted_information():
    result = run("096_three_colors")
    assert result["all_ternary_worlds_lengths_one_through_eight"] == 9840
    assert result["seeded_hundred_person_worlds"] == 1000
    assert result["indistinguishable_first_speaker_view_classes"] == 243
