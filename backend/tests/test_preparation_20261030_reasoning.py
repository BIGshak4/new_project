"""Independent mathematical checks for three new October30 source questions."""
import importlib.util
from pathlib import Path

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def run_check(number):
    spec = importlib.util.spec_from_file_location(f"intake1030_reasoning_{number}", BANK / f"checks/check_prep_{number}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_checks()


def test_equal_return_volume_conserves_foreign_amount_even_without_mixing():
    result = run_check(143)
    assert result["mixed_exact_cases"] == 1080
    assert result["equal_initial_volume_cases"] == 90
    assert result["arbitrary_return_composition_cases"] == 4447
    assert result["invalid_cases_rejected"] == 5


def test_sampling_aliases_match_independent_frequency_and_tone_oracles():
    result = run_check(144)
    assert result["frequency_folding_cases"] == 8005
    assert result["sampled_cosine_comparisons"] == 136085
    assert result["nyquist_boundary_zero_sine_samples"] == 32
    assert result["indistinguishable_38khz_10khz_samples_at_48ksps"] == 128
    assert result["invalid_cases_rejected"] == 4


def test_finite_equal_distance_round_trip_never_reaches_twice_first_speed():
    result = run_check(146)
    assert result["exact_trip_cases"] == 4800
    assert result["attainable_target_ratio_cases"] == 5400
    assert result["limit_sequence_examples"] == 5
    assert result["invalid_cases_rejected"] == 6
