"""Finite independent logic checks and durable bilingual asset contracts."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import struct
from datetime import date
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
BANK=ROOT/"interview_preparation"
NEW={"PREP-231","PREP-232"}


def load(filename,folder="solutions"):
    spec=importlib.util.spec_from_file_location("batch22_"+filename,BANK/folder/(filename+".py"))
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.fixture(scope="module")
def checked():
    return load("check_batch22_logic_20261031","checks").check_all()


@pytest.mark.parametrize("ident",["PREP-231","PREP-232","PREP-025","PREP-017"])
def test_independent_finite_models_match_saved_reports(ident,checked):
    suffix=ident.lower()+("-batch22" if ident in {"PREP-025","PREP-017"} else "")
    assert checked[ident]==json.loads((BANK/"checks"/(suffix+"-verification.json")).read_bytes())
    assert checked[ident]["status"]=="pass"


def test_exhaustion_domains_and_reference_examples_are_explicit(checked):
    assert checked["PREP-025"]["threshold_scenarios"]==10201
    assert checked["PREP-017"]["distinct_minutes_exhausted"]==720
    assert checked["PREP-017"]["periodicity_comparisons"]==720
    assert checked["PREP-231"]["identity_decisions_checked"]==1024
    assert checked["PREP-231"]["hundred_lion_initial_cow_eaten"] is False
    assert checked["PREP-232"]["date_birthday_pairs_checked"]==400040
    assert checked["PREP-232"]["calendar_years_enumerated"]==[2023,2024,2025]
    assert checked["PREP-232"]["timeline_ages"]==[8,9,9,10,11]


@pytest.mark.parametrize("bad",[-1,True,1.5,"100"])
def test_lion_count_rejects_inputs_outside_contract(bad):
    module=load("prep_231_rational_lions_cow")
    with pytest.raises(ValueError):
        module.cow_is_eaten(bad)
    with pytest.raises(ValueError):
        module.outcome(bad)


@pytest.mark.parametrize("bad",[-1,True,1.5,"10"])
def test_egg_count_rejects_inputs_outside_contract(bad):
    with pytest.raises(ValueError):
        load("prep_025_highest_safe_floor_batch22").minimum_drops(bad)


def test_safe_floor_is_not_first_break_and_top_knowledge_matters():
    model=load("prep_025_highest_safe_floor_batch22")
    assert model.highest_safe_floor(10,lambda floor:floor>=6)==5
    assert model.highest_safe_floor(10,lambda floor:False)==10
    assert model.highest_safe_floor(10,lambda floor:True)==0
    assert model.highest_safe_floor(0,lambda floor:pytest.fail("No drop in an empty building"))==0
    assert model.minimum_drops(2)==2
    assert model.minimum_drops(2,top_known_breaking=True)==1
    with pytest.raises(ValueError):
        model.minimum_drops(0,top_known_breaking=True)


@pytest.mark.parametrize("hour,minute,error",[(24,0,ValueError),(-1,0,ValueError),(0,60,ValueError),(0,-1,ValueError),(True,0,TypeError),(1,0.5,TypeError)])
def test_clock_input_boundaries(hour,minute,error):
    with pytest.raises(error):
        load("prep_017_general_clock_batch22").minor_angle(hour,minute)


def test_age_timeline_and_birthdays_use_calendar_boundaries():
    model=load("prep_232_calendar_age")
    timeline=model.age_timeline(2026)
    assert timeline["two_days_ago"]=={"date":"2025-12-30","age":8}
    assert timeline["today"]=={"date":"2026-01-01","age":9}
    assert timeline["birthday_this_year"]["age"]==10
    assert timeline["birthday_next_year"]["age"]==11
    assert model.age_on(date(2016,12,31),date(2025,12,31))==9
    assert model.age_on(date(2016,12,31),date(2026,1,2))==9
    with pytest.raises(ValueError):
        model.age_on(date(2016,12,31),date(2015,1,1))


@pytest.mark.parametrize("stem",["prep-025-highest-safe-batch22","prep-017-general-clock-batch22","prep-231-lion-survival-parity","prep-232-calendar-age-timeline"])
def test_clean_original_bilingual_png_pairs_exist(stem):
    hashes=[]
    for lang in ("he","en"):
        data=(BANK/"diagrams"/f"{stem}-{lang}.png").read_bytes()
        assert data[:8]==b"\x89PNG\r\n\x1a\n"
        width,height=struct.unpack(">II",data[16:24])
        assert width>=2000 and height>=1200
        hashes.append(hashlib.sha256(data).hexdigest())
    assert hashes[0]!=hashes[1]


@pytest.mark.parametrize("path",["prep-231-rational-lions-cow-survival-parity.md","prep-232-calendar-age-two-days-ago-next-year.md","prep-025-highest_safe_batch22-addendum.md","prep-017-general_clock_batch22-addendum.md"])
def test_owned_markdown_contains_full_bilingual_material_and_models(path):
    text=(BANK/"questions"/path).read_text("utf-8")
    assert "## עברית" in text and "## English" in text
    assert text.count("```python")>=2
    fields=json.loads(text.rsplit("```json\n",1)[1].split("\n```",1)[0])
    assert set(fields)>={"assumptions","optimality","verification","edge_cases","common_mistakes","interview_answer","source_ambiguities","solution_extensions"}
    for name,values in fields.items():
        assert set(values)=={"he","en"}
        assert values["he"] and values["en"],name
        assert re.search(r"[\u05d0-\u05ea]",json.dumps(values["he"],ensure_ascii=False))
        assert not re.search(r"[\u05d0-\u05ea]",json.dumps(values["en"],ensure_ascii=False))


def test_archived_new_logic_records_have_three_hints_and_correct_provenance():
    archive={q["id"]:q for q in json.loads((BANK/"questions.json").read_bytes())["questions"]}
    for ident in NEW:
        q=archive[ident]
        assert q["version"]==1 and q["category"]=="logic"
        assert q["reviewed_by"] is None and q["solution_status"]=="proposed"
        assert q["difficulty"] is q["estimated_minutes"] is None
        assert q["reported_companies"]==["Apple"]
        assert (BANK/q["solution_code_path"]).is_file()
        assert (BANK/q["verification_result_path"]).is_file()
        for lang in ("he","en"):
            t=q["translations"][lang]
            assert len(t["hints"])==len(set(t["hints"]))==3
            assert t["hint"]==t["hints"][0]
            assert not any(word in t["prompt"].casefold() for word in ("צילום","screenshot","user requested"))
