"""Exact transport and physical-front oracles for two source-backed puzzles."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"


def load_check(number):
    spec = importlib.util.spec_from_file_location(f"batch11_check_{number}", BANK / f"checks/check_prep_{number}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_camel_transport_conservation_and_independent_integer_road_search():
    result = load_check(121).run_checks()
    assert result["continuous_delivery"] == "1600/3"
    assert result["whole_banana_delivery"] == 533
    assert result["canonical_plan_move_legs_each"] == 9
    assert result["canonical_conservation_events"] == 43
    assert result["small_integer_road_cases"] == 105
    assert result["exhaustively_explored_states"] == 1263
    assert result["integer_relaxation_equalities"] == 76


def test_nonuniform_spatial_flames_match_independent_burn_time_coordinates():
    result = load_check(124).run_checks()
    assert result["first_event_minutes"] == 30
    assert result["final_event_minutes"] == 45
    assert result["exhaustive_profiles"] == 26
    assert result["exhaustive_profile_pair_directions"] == 1352
    assert result["seeded_profile_pair_directions"] == 800
    assert result["invalid_cases_rejected"] == 7


@pytest.mark.parametrize("number,source,companies", [(121, 5, ["Mellanox", "Apple"]), (124, 9, ["Applied Materials"])])
def test_bilingual_logic_content_has_sourced_unrated_proposed_material(number, source, companies):
    archive = json.loads((BANK / "questions.json").read_text(encoding="utf-8"))
    question = next(q for q in archive["questions"] if q["id"] == f"PREP-{number}")
    assert question["status"] == "in_review" and question["solution_status"] == "proposed"
    assert question["reviewed_by"] is None and question["difficulty"] is None
    assert question["ai_assisted"] is True and question["reported_companies"] == companies
    assert question["sources"][0]["path"] == f"sources/2026-10-25-batch11-{source:02}.png"
    for language in ("he", "en"):
        localized = question["translations"][language]
        assert len(localized["hints"]) == len(set(localized["hints"])) == 3
        assert [hint["content"] for hint in question["prepared_hints"] if hint["language"] == language] == localized["hints"]
        diagrams = [asset for asset in question["media_assets"] if asset.get("language") == language]
        assert len(diagrams) == 1 and diagrams[0]["type"] == "solution_diagram"
        assert (BANK / diagrams[0]["path"]).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
