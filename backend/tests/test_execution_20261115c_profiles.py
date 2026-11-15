"""Runtime contracts use input-only fixtures, independent oracles and exact old profiles."""
import copy
import json
import runpy
import subprocess
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
BACKEND=ROOT/'backend'
FIXTURES=BACKEND/'tests/fixtures'
AUTHOR=runpy.run_path(str(FIXTURES/'execution_catalog_authoring.py'))
INPUTS=json.loads((FIXTURES/'execution_batch1115c_inputs.json').read_bytes())
MANIFEST=json.loads((BACKEND/'seeds/execution_cases.json').read_bytes())['questions']
SMOKE=json.loads((FIXTURES/'execution_smoke.json').read_bytes())['cases']


@pytest.mark.parametrize('key', sorted(INPUTS))
def test_input_only_cases_have_independent_expected_values_and_reject_wrong_fixture(key):
    given=INPUTS[key]['languages']['python']
    built=MANIFEST[key]['languages']['python']
    assert len(given['cases'])==len(built['cases'])==12
    namespace={}
    exec(compile(AUTHOR['batch1115c_source'](key),key,'exec'),namespace)
    reference=namespace[built['entry']]
    for original,case in zip(given['cases'],built['cases'],strict=True):
        assert set(original)=={'args'} and original['args']==case['args']
        before=copy.deepcopy(original['args'])
        expected=AUTHOR['ORACLES'][key](*copy.deepcopy(before))
        assert expected==case['expected']==reference(*copy.deepcopy(before))
        assert original['args']==before
    wrong=next(row for row in SMOKE if row['question_key']==key)['wrong']
    namespace={}
    exec(compile(wrong,'<wrong>','exec'),namespace)
    assert any(namespace[built['entry']](*copy.deepcopy(case['args']))!=case['expected']
               for case in built['cases'])


def test_all_fifty_nine_previous_profiles_and_current_totals_are_exact():
    prior=json.loads(subprocess.check_output(['git','show',
        'c44202c0c5fc6e8087cdff5399cc933118f68cf8:backend/seeds/execution_cases.json'],cwd=ROOT))['questions']
    assert len(prior)==59 and len(MANIFEST)==66
    assert all(MANIFEST[key]==spec for key,spec in prior.items())
    assert set(MANIFEST)-set(prior)-set(AUTHOR['BATCH1115D_SOURCES'])==set(INPUTS)


def test_pyramid_streaming_matches_full_reference_and_preserves_inputs():
    namespace={}
    exec(compile(AUTHOR['batch1115c_source']('prep-blur-subsample-pyramid-and-row-streaming'),
                 '<pyramid>','exec'),namespace)
    image=[[0,9],[18,27]]
    assert namespace['collect_stream_pyramid'](image,1)==[image,[[9]]]
    assert image==[[0,9],[18,27]]


def test_grid_coincidence_does_not_hide_an_additional_forbidden_pair():
    namespace={}
    exec(compile(AUTHOR['batch1115c_source']('prep-finite-colored-sampling-grid-validation'),
                 '<grids>','exec'),namespace)
    green=[0,0,1,1,1,1]
    assert namespace['colored_grids_valid'](5,5,green,green)
    assert not namespace['colored_grids_valid'](5,5,green,[0,0,2,1,2,1])
