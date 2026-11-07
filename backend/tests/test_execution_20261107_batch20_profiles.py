"""New deterministic execution profiles; no learner submissions are executed."""
from __future__ import annotations

import ast
import copy
import json
import runpy
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
AUTHORING = runpy.run_path(str(BACKEND / 'tests/fixtures/execution_catalog_authoring.py'))
INPUTS = json.loads((BACKEND / 'tests/fixtures/execution_batch1107b20_inputs.json').read_bytes())
MANIFEST = json.loads((BACKEND / 'seeds/execution_cases.json').read_bytes())['questions']
POSITIVE = json.loads((BACKEND / 'tests/fixtures/execution_positive.json').read_bytes())['cases']
SMOKE = json.loads((BACKEND / 'tests/fixtures/execution_smoke.json').read_bytes())['cases']
COUNTS = {'prep-circular-packed-bit-array-move': 10,
          'prep-reverse-signed-decimal-integer': 15,
          'prep-relative-sort-by-second-array': 12}
CASES = [(key, case) for key in COUNTS for case in MANIFEST[key]['languages']['python']['cases']]


def reference(key):
    fixture = next(row for row in POSITIVE if row['question_key'] == key)
    scope = {}
    exec(compile(fixture['source'], '<trusted-batch20-reference>', 'exec'), scope)
    return scope[MANIFEST[key]['languages']['python']['entry']]


@pytest.mark.parametrize('key', COUNTS)
def test_input_only_fixtures_and_independent_expected_values(key):
    assert set(INPUTS) == set(AUTHORING['BATCH1107B20_ORACLES']) == set(COUNTS)
    given = INPUTS[key]['languages']['python']
    built = MANIFEST[key]['languages']['python']
    assert len(built['cases']) == len(given['cases']) == COUNTS[key]
    assert all(set(case) == {'args'} for case in given['cases'])
    assert [case['args'] for case in built['cases']] == [case['args'] for case in given['cases']]
    assert all(case['expected'] == AUTHORING['BATCH1107B20_ORACLES'][key](*case['args'])
               for case in built['cases'])


@pytest.mark.parametrize('key,case', CASES)
def test_authored_reference_against_each_independent_case(key, case):
    args = copy.deepcopy(case['args'])
    before = copy.deepcopy(args)
    result = reference(key)(*args)
    assert result == case['expected']
    if key == 'prep-circular-packed-bit-array-move':
        assert result is args[0]
        assert all(0 <= v <= 255 for v in result)
    else:
        assert args == before


@pytest.mark.parametrize('key', COUNTS)
def test_wrong_and_syntax_fixtures_fail(key):
    fixture = next(row for row in SMOKE if row['question_key'] == key)
    with pytest.raises(SyntaxError):
        compile(fixture['syntax_error'], '<intentional-invalid-batch20>', 'exec')
    scope = {}
    exec(compile(fixture['wrong'], '<trusted-intentional-wrong-batch20>', 'exec'), scope)
    entry = MANIFEST[key]['languages']['python']['entry']
    assert any(scope[entry](*copy.deepcopy(case['args'])) != case['expected']
               for case in MANIFEST[key]['languages']['python']['cases'])


def test_domain_rejections_and_no_mutation_on_invalid_packed_input():
    move = reference('prep-circular-packed-bit-array-move')
    values = [0] * 128
    for x, y in [(-1, 0), (0, 1024), (True, 1)]:
        with pytest.raises(ValueError):
            move(values, x, y)
        assert values == [0] * 128
    with pytest.raises(ValueError):
        reference('prep-reverse-signed-decimal-integer')(1 << 31)
    with pytest.raises(ValueError):
        reference('prep-relative-sort-by-second-array')([1], [1, 1])


def test_candidate_structural_constraints_and_excluded_nonfunction_models():
    move = ast.parse(AUTHORING['batch1107b20_source']('prep-circular-packed-bit-array-move'))
    assert not any(isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)) for node in ast.walk(move))
    reverse = ast.parse(AUTHORING['batch1107b20_source']('prep-reverse-signed-decimal-integer'))
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'str'
                   for node in ast.walk(reverse))
    assert 'prep-kmeans-explain-and-lloyd-iterations' not in MANIFEST
    assert 'prep-test-and-set-spinlock' not in MANIFEST
    for key in COUNTS:
        assert len([row for row in POSITIVE if row['question_key'] == key]) == 1
        assert len([row for row in SMOKE if row['question_key'] == key]) == 1
