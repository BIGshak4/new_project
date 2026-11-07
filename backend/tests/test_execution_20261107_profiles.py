"""Input-only, oracle-derived runtime profiles for the two November 7 predicates."""
from __future__ import annotations

import json
import runpy
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
AUTHORING = runpy.run_path(str(BACKEND / 'tests/fixtures/execution_catalog_authoring.py'))
INPUTS = json.loads((BACKEND / 'tests/fixtures/execution_batch1107_inputs.json').read_bytes())
MANIFEST = json.loads((BACKEND / 'seeds/execution_cases.json').read_bytes())['questions']
SMOKE = json.loads((BACKEND / 'tests/fixtures/execution_smoke.json').read_bytes())['cases']


def test_inputs_contain_no_expected_values_and_rebuild_from_separate_oracles():
    assert set(INPUTS) == set(AUTHORING['BATCH1107_ORACLES'])
    for key, question in INPUTS.items():
        spec = question['languages']['python']
        assert all(set(case) == {'args'} for case in spec['cases'])
        built = MANIFEST[key]['languages']['python']
        assert [case['args'] for case in built['cases']] == [case['args'] for case in spec['cases']]
        for case in built['cases']:
            assert case['expected'] == AUTHORING['BATCH1107_ORACLES'][key](*case['args'])


@pytest.mark.parametrize('key', sorted(INPUTS))
def test_wrong_and_invalid_sources_are_detected(key):
    fixture = next(case for case in SMOKE if case['question_key'] == key)
    with pytest.raises(SyntaxError):
        compile(fixture['syntax_error'], '<syntax-probe>', 'exec')
    scope = {}
    exec(compile(fixture['wrong'], '<trusted-wrong-probe>', 'exec'), scope)
    spec = MANIFEST[key]['languages']['python']
    assert any(scope[spec['entry']](*case['args']) != case['expected'] for case in spec['cases'])


def test_profiles_keep_their_actual_guarantees_explicit():
    prime = MANIFEST['prep-primality-predicate-finite-input-domain']
    speed = MANIFEST['prep-branch-free-saturating-speed-controls']
    assert len(prime['languages']['python']['cases']) == 16
    assert len(speed['languages']['python']['cases']) == 11
    assert 'hardware' in prime['contract']['en']
    assert {case['args'][0] for case in speed['languages']['python']['cases']} == set(range(11))
