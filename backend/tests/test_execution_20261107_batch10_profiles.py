"""Input-only, independently expected general-sort execution profile."""
from __future__ import annotations

import ast
import copy
import json
import runpy
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
AUTHORING = runpy.run_path(str(BACKEND / 'tests/fixtures/execution_catalog_authoring.py'))
INPUTS = json.loads((BACKEND / 'tests/fixtures/execution_batch1107b10_inputs.json').read_bytes())
MANIFEST = json.loads((BACKEND / 'seeds/execution_cases.json').read_bytes())['questions']
POSITIVE = json.loads((BACKEND / 'tests/fixtures/execution_positive.json').read_bytes())['cases']
SMOKE = json.loads((BACKEND / 'tests/fixtures/execution_smoke.json').read_bytes())['cases']
KEY = 'prep-general-in-place-integer-array-sort'


def test_sort_inputs_have_no_answers_and_outputs_come_from_independent_oracle():
    assert set(INPUTS) == set(AUTHORING['BATCH1107B10_ORACLES']) == {KEY}
    inputs = INPUTS[KEY]['languages']['python']['cases']
    built = MANIFEST[KEY]['languages']['python']
    assert built['entry'] == 'sort_array' and len(inputs) == len(built['cases']) == 14
    assert all(set(case) == {'args'} for case in inputs)
    assert [case['args'] for case in built['cases']] == [case['args'] for case in inputs]
    for case in built['cases']:
        assert case['expected'] == AUTHORING['BATCH1107B10_ORACLES'][KEY](*case['args'])


@pytest.mark.parametrize('case', MANIFEST[KEY]['languages']['python']['cases'])
def test_saved_positive_reference_sorts_in_the_same_list(case):
    fixture = next(row for row in POSITIVE if row['question_key'] == KEY)
    scope = {}
    exec(compile(fixture['source'], '<trusted-sort-reference>', 'exec'), scope)
    args = copy.deepcopy(case['args'])
    original_list = args[0]
    result = scope['sort_array'](*args)
    assert result is original_list
    assert result == case['expected']


def test_reference_has_no_builtin_sort_recursion_or_input_sized_comprehension():
    source = AUTHORING['batch1107b10_source'](KEY)
    tree = ast.parse(source)
    assert not any(isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)) for node in ast.walk(tree))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert not any(isinstance(node.func, ast.Name) and node.func.id in ('sort_array', 'sorted') for node in calls)
    assert not any(isinstance(node.func, ast.Attribute) and node.func.attr == 'sort' for node in calls)
    assert 'Output checks alone do not prove' in MANIFEST[KEY]['contract']['en']


def test_invalid_syntax_and_unchanged_wrong_output_are_detected():
    fixture = next(row for row in SMOKE if row['question_key'] == KEY)
    with pytest.raises(SyntaxError):
        compile(fixture['syntax_error'], '<invalid-sort>', 'exec')
    scope = {}
    exec(compile(fixture['wrong'], '<trusted-wrong-sort>', 'exec'), scope)
    assert any(scope['sort_array'](*copy.deepcopy(case['args'])) != case['expected']
               for case in MANIFEST[KEY]['languages']['python']['cases'])


def test_only_general_sort_is_added_and_subset_sum_has_no_overriding_profile():
    assert set(AUTHORING['BATCH1107B10_SOURCES']) == {KEY}
    assert AUTHORING['BATCH1107B10_SOURCES'][KEY] == 'prep_273_heapsort_batch1107b10.py'
    assert not any('subset' in key for key in MANIFEST)
    assert (ROOT / 'interview_preparation/solutions/prep_040_subset_sum_batch1107b10.py').exists()
    assert len([row for row in POSITIVE if row['question_key'] == KEY]) == 1
    assert len([row for row in SMOKE if row['question_key'] == KEY]) == 1
