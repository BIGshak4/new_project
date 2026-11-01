"""Finite Python/fuel oracles and publication contracts for five concept records."""
from __future__ import annotations

import importlib.util
import json
import struct
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / 'interview_preparation'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def checks():
    return load(BANK / 'checks/check_batch20_concepts_20261101.py', 'batch20_concepts_checks')


@pytest.mark.parametrize('number', [240, 241, 242, 243, 244])
def test_executed_checks_reproduce_reports_without_inventing_native_execution(checks, number):
    actual = checks.CHECKS[number]()
    assert actual == json.loads((BANK / f'checks/prep-{number}-verification.json').read_bytes())
    assert actual['status'] == 'pass' and actual['professional_review'] == 'pending'
    assert not any(actual[key] for key in ['c_compiled', 'cpp_compiled', 'csharp_executed', 'java_executed'])
    if number in (240, 241):
        assert actual['cases'] == 0 and not actual['python_executed']
        assert actual['verification_kind'] == 'primary_document_review'


def test_motorcycle_plan_is_not_the_false_all_fuel_on_one_bike_bound(checks):
    model = checks.load('prep_244_motorcycle_fuel_plan')
    assert model.max_distance(2, 50) == 75
    assert model.max_distance(3, 50) == Fraction(275, 3)
    assert model.max_distance(100, 50) < 5000
    assert model.max_distance(100, 50, 2) == model.max_distance(100, 50) / 2
    assert model.plan(0) == (0, [])


@pytest.mark.parametrize('arguments', [(-1, 50, 1), (True, 50, 1), (1, 0, 1), (1, 50, 0), (1, 50, -1)])
def test_invalid_fuel_contracts_are_rejected(checks, arguments):
    model = checks.load('prep_244_motorcycle_fuel_plan')
    for function in (model.plan, model.max_distance):
        with pytest.raises(ValueError):
            function(*arguments)


def test_python_examples_really_exercise_runtime_failures_and_shadowing(checks):
    actual = checks.load('prep_242_python_oop_examples').examples()
    assert actual['incompatible_addition'] == actual['last_definition_replaces_first'] == 'TypeError'
    assert actual['annotation_not_enforced'] == 'text'
    assert actual['mangled_name_accessible'] == 7
    assert actual['class_attribute_shared'] == actual['shadow_does_not_replace_class_attribute']
    assert actual['instance_attribute_separate'] == []


@pytest.mark.parametrize('number', [240, 241, 242, 243, 244])
def test_both_clean_diagrams_are_large_nonempty_pngs(number):
    images = [(BANK / f'diagrams/prep-{number}-concepts-{lang}.png').read_bytes() for lang in ('he', 'en')]
    assert images[0] != images[1]
    for image in images:
        assert image.startswith(b'\x89PNG\r\n\x1a\n')
        assert struct.unpack('>II', image[16:24]) == (2400, 1400)
        assert len(image) > 15000


def test_archived_five_records_keep_actual_source_companies_and_bilingual_material():
    archive = {q['id']: q for q in json.loads((BANK / 'questions.json').read_bytes())['questions']}
    expected = {240: ('Check Point', 16), 241: ('Rafael', 18), 242: ('Apple', 19),
                243: ('Apple', 20), 244: ('Mellanox', 14)}
    for number, (company, screenshot) in expected.items():
        q = archive[f'PREP-{number}']
        assert q['version'] == 1 and q['ai_assisted'] and q['reviewed_by'] is None
        assert q['solution_status'] == 'proposed' and q['difficulty'] is q['estimated_minutes'] is None
        assert q['reported_companies'] == [company]
        assert any(s['path'] == f'sources/2026-11-01-batch20-{screenshot:02d}.png' for s in q['sources'])
        assert (BANK / q['markdown_path']).is_file()
        assert len(q['prepared_hints']) == 6
        for lang in ('he', 'en'):
            assert len(q['translations'][lang]['hints']) == len(set(q['translations'][lang]['hints'])) == 3
            assert q['translations'][lang]['reference_solution']
