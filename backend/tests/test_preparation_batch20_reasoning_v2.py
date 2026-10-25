"""New25-Oct affine-model, local-information and first-contact puzzle checks."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"


def load_check(number):
    spec = importlib.util.spec_from_file_location(f"reasoning_v2_check_{number}", BANK / f"checks/check_prep_{number}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_affine_cooling_keeps_temperature_slope_and_heat_power_contracts_distinct():
    result = load_check(126).run_checks()
    assert result["equal_temperature_slope_cases"] == 486
    assert result["constant_power_energy_cases"] == 486
    assert result["general_postmix_slope_cases"] == 1458
    assert result["distinct_valid_comparison_signs"] == 3
    assert result["invalid_cases_rejected"] == 6


def test_distributed_hat_controller_and_every_binary_local_protocol():
    result = load_check(127).run_checks()
    assert result["exhaustive_worlds_n1_to_n5"] == 3413
    assert result["ten_color_worlds"] == 10004
    assert result["binary_local_protocol_pairs"] == 16
    assert result["universally_winning_binary_protocols"] == 2
    assert result["invalid_cases_rejected"] == 6


def test_snail_first_contact_ends_before_final_rest_and_matches_global_time_path():
    result = load_check(129).run_checks()
    assert result["first_contact_minutes"] == 17
    assert result["climbs"] == 9 and result["completed_rests"] == 8
    assert result["independent_global_time_grid_cases"] == 300
    assert result["fractional_height_cases"] == 3
    assert result["invalid_cases_rejected"] == 5


@pytest.mark.parametrize("number,source,companies", [
    (126, 1, ["Applied Materials"]), (127, 3, ["NVIDIA", "Mellanox"]), (129, 7, ["NVIDIA"]),
])
def test_new_bilingual_logic_content_is_sourced_proposed_and_solution_media_gated(number, source, companies):
    archive = json.loads((BANK / "questions.json").read_text(encoding="utf-8"))
    record = next(q for q in archive["questions"] if q["id"] == f"PREP-{number}")
    assert record["status"] == "in_review" and record["solution_status"] == "proposed"
    assert record["reviewed_by"] is None and record["difficulty"] is None
    assert record["ai_assisted"] is True
    assert record["reported_companies"] == companies
    assert record["sources"][0]["path"] == f"sources/2026-10-25-batch20-{source:02}.png"
    for language in ("he", "en"):
        text = record["translations"][language]
        assert len(text["hints"]) == len(set(text["hints"])) == 3
        assert [h["content"] for h in record["prepared_hints"] if h["language"] == language] == text["hints"]
        diagrams = [a for a in record["media_assets"] if a.get("language") == language]
        assert len(diagrams) == 1 and diagrams[0]["type"] == "solution_diagram"
        assert (BANK / diagrams[0]["path"]).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
