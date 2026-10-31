"""Durable content/truth/timing contracts for seven combinational intake records.

These run finite independent Python oracles, not RTL, physical timing or safety
qualification. Existing question/source identities are intentionally preserved.
"""
from __future__ import annotations

import importlib.util
import json
import re
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds/preparation_localization"
NEW = {"PREP-213", "PREP-214", "PREP-215"}
VARIANTS = {"PREP-070", "PREP-083", "PREP-107", "PREP-110"}
IDS = sorted(NEW | VARIANTS)
FIELDS = {"assumptions", "optimality", "verification", "edge_cases", "common_mistakes",
          "interview_answer", "source_ambiguities", "solution_extensions"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


@pytest.fixture(scope="module")
def archive():
    return {q["id"]: q for q in read(BANK / "questions.json")["questions"]}


@pytest.fixture(scope="module")
def model_results():
    path = BANK / "checks/check_batch20_combinational_20261031.py"
    spec = importlib.util.spec_from_file_location("batch20_combinational_checks", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.check_all()


@pytest.mark.parametrize("ident", IDS)
def test_exhaustive_independent_checks_match_persisted_evidence(ident, model_results):
    result = model_results[ident]
    assert result == read(BANK / f"checks/{ident.lower()}-batch20-verification.json")
    assert result["status"] == "pass"


def test_large_truth_domains_and_declared_timing_are_actually_checked(model_results):
    lsb = model_results["PREP-107"]
    assert lsb["exhaustive_20_bit_words_per_network"] == 2**20
    assert lsb["networks"] == 2 and lsb["timing_outputs_checked"] == 20
    assert lsb["serial_delay_ns"] == 20
    assert lsb["balanced_delay_bound_ns"] == 7 <= 10
    compare = model_results["PREP-110"]
    assert compare["exhaustive_unsigned_operand_pairs_per_network"] == sum(4**n for n in range(1, 9))
    assert compare["authorized_one_bit_completion_rows"] == 4
    add = model_results["PREP-215"]
    assert add["maximum_unsigned_sum"] == 18 and add["minimum_result_width"] == 5
    assert (add["ripple_delay_ns"], add["carry_select_delay_ns"],
            add["unrestricted_zero_delay_mux_tree_delay_ns"]) == (4, 2, 0)
    assert add["exhaustive_operand_pairs_per_architecture"] == 64 and add["architectures"] == 3
    assert model_results["PREP-083"]["master_slave_trace_steps"] == 8192


@pytest.mark.parametrize("ident", sorted(NEW))
def test_new_records_keep_review_state_three_hints_and_traceable_assets(ident, archive):
    q = archive[ident]
    assert q["status"] == "in_review" and q["solution_status"] == "proposed"
    assert q["reviewed_by"] is None and q["ai_assisted"] is True
    assert q["difficulty"] is None and q["estimated_minutes"] is None
    assert q["original_prompt"].strip()
    assert q["reported_companies"] == (["NVIDIA"] if ident == "PREP-213" else ["Cisco"])
    assert q["follow_up_integration_status"] == "prepared_in_archive_not_connected_to_interactive_queue"
    for language in ("he", "en"):
        t = q["translations"][language]
        assert len(t["hints"]) == 3 and len(set(t["hints"])) == 3
        assert t["hint"] == t["hints"][0]
        assert all(t[field].strip() for field in ("title", "prompt", "reference_solution"))
        prepared = [h for h in q["prepared_hints"] if h["language"] == language]
        assert [h["level"] for h in prepared] == [1, 2, 3]
        assert [h["content"] for h in prepared] == t["hints"]
        if language == "en":
            assert not re.search(r"[\u0590-\u05ff]", t["prompt"] + t["reference_solution"])
    assert (BANK / q["markdown_path"]).is_file()
    assert (BANK / q["solution_code_path"]).is_file()
    assert (BANK / q["verification_script_path"]).is_file()


def test_all_eight_material_fields_are_present_in_both_languages():
    localization = {}
    for path in sorted(SEEDS.glob("*.json")):
        entries = read(path)
        assert not localization.keys() & entries.keys(), path
        localization.update(entries)
    for ident in IDS:
        assert localization[ident].keys() >= FIELDS
        for field in FIELDS:
            values = localization[ident][field]
            assert values["he"] and values["en"], (ident, field)
            assert re.search(r"[\u0590-\u05ff]", json.dumps(values["he"], ensure_ascii=False)), (ident, field)
            assert not re.search(r"[\u0590-\u05ff]", json.dumps(values["en"], ensure_ascii=False)), (ident, field)


def test_source_mux_mapping_and_unrestricted_zero_delay_model_are_explicit(archive):
    mux = archive["PREP-214"]["translations"]["en"]
    assert "D0=Q3,D1=Q2" in mux["prompt"]
    assert "D0=Q1,D1=Q0" in mux["prompt"]
    assert "U = MUX(S0,Q3,Q2)" in mux["reference_solution"]
    assert "U=MUX(S0,Q0,Q1)" in mux["reference_solution"]
    assert "m+1" in mux["reference_solution"]
    adder = archive["PREP-215"]["translations"]["en"]["reference_solution"]
    assert "**5 bits**" in adder and "not 6" in adder
    assert "0 ns" in adder and "unrestricted model" in adder
    assert "six FAs and three MUXes" in adder


def test_extension_contracts_keep_restrictions_and_truncation_visible(archive):
    alert = archive["PREP-213"]["translations"]["en"]["prompt"]
    assert "functional alert" in alert and "brake-actuation" in alert
    gates = archive["PREP-070"]["translations"]["en"]["reference_solution"]
    assert "NAND = MUX(A,1,nB)" in gates and "shared" in gates
    storage = archive["PREP-083"]["translations"]["en"]["reference_solution"]
    assert "does not establish actual nonoverlap" in storage and "nCLK=MUX(CLK,1,0)" in storage
    lsb = archive["PREP-107"]["translations"]["en"]["reference_solution"]
    assert "7 ns" in lsb and "20 ns" in lsb and "free" in lsb.lower()
    compare = archive["PREP-110"]["translations"]["en"]
    assert "explicitly requested by the user" in compare["prompt"]
    assert "not a verified reconstruction" in compare["prompt"]
    assert "g[-1]=0" in compare["reference_solution"]
    assert "Y=NOT A AND B" in compare["reference_solution"]
    assert "The source stops" in compare["reference_solution"]


@pytest.mark.parametrize("ident", IDS)
def test_original_bilingual_schematic_pngs_are_readable_native_assets(ident):
    for language in ("he", "en"):
        path = BANK / f"diagrams/{ident.lower()}-combinational-batch20-{language}.png"
        raw = path.read_bytes()
        assert raw[:8] == b"\x89PNG\r\n\x1a\n"
        width, height = struct.unpack(">II", raw[16:24])
        assert width >= 2000 and height >= 1200
        assert len(raw) > 15000
