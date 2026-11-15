"""Exact decimal grids and branch-free/cross-array runtime contracts."""
import ast
import copy
import json
import runpy
import subprocess
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
BACKEND=ROOT/'backend'
F=BACKEND/'tests/fixtures'
AUTHOR=runpy.run_path(str(F/'execution_catalog_authoring.py'))
INPUTS=json.loads((F/'execution_batch1115d_inputs.json').read_bytes())
MANIFEST=json.loads((BACKEND/'seeds/execution_cases.json').read_bytes())['questions']
SMOKE=json.loads((F/'execution_smoke.json').read_bytes())['cases']


@pytest.mark.parametrize('key',sorted(INPUTS))
def test_input_only_profiles_use_independent_oracles_and_discriminate_wrong_sources(key):
    given=INPUTS[key]['languages']['python']
    built=MANIFEST[key]['languages']['python']
    namespace={}
    exec(compile(AUTHOR['batch1115d_source'](key),key,'exec'),namespace)
    reference=namespace[built['entry']]
    assert 12<=len(given['cases'])==len(built['cases'])<=32
    for original,case in zip(given['cases'],built['cases'],strict=True):
        assert set(original)=={'args'} and original['args']==case['args']
        args=copy.deepcopy(original['args'])
        expected=AUTHOR['ORACLES'][key](*copy.deepcopy(args))
        assert expected==case['expected']==reference(*args)
        assert args==original['args']
    smoke=next(row for row in SMOKE if row['question_key']==key)
    wrong={};exec(compile(smoke['wrong'],'<wrong>','exec'),wrong)
    assert any(wrong[built['entry']](*copy.deepcopy(case['args']))!=case['expected']
               for case in built['cases'])
    with pytest.raises(SyntaxError):compile(smoke['syntax_error'],'<syntax>','exec')


def test_all_sixty_three_previous_profiles_are_unchanged():
    prior=json.loads(subprocess.check_output(['git','show',
        '397947d1cb08587b4f6705ff2b5f5bd33d8aebb4:backend/seeds/execution_cases.json'],cwd=ROOT))['questions']
    assert len(prior)==63 and len(MANIFEST)==66
    assert all(MANIFEST[key]==spec for key,spec in prior.items())
    assert set(MANIFEST)-set(prior)==set(INPUTS)


def test_voltage_runtime_distinguishes_strict_grid_values_from_off_grid_and_endpoints():
    key='prep-first-failure-exact-decimal-voltage-grid'
    namespace={};exec(AUTHOR['batch1115d_source'](key),namespace)
    fn=namespace['first_failure_voltage']
    assert fn('0','0.3','0.1',['0','0.3']) is None
    assert fn('0','1','0.1',['0.8','0.30'])==[3,10]
    assert fn('0','1','0.2',['0.3']) is None
    assert fn('1e20','100000000000000000001','0.125',
              ['100000000000000000000.375'])==[800000000000000000003,8]


def test_bit_witness_source_has_no_disguised_condition_and_handles_uint32_edges():
    key='prep-branch-free-uint32-different-from-two-inputs'
    source=AUTHOR['batch1115d_source'](key)
    forbidden=(ast.If,ast.IfExp,ast.Compare,ast.For,ast.While,ast.Match,ast.BoolOp,ast.Call,ast.Subscript)
    assert not any(isinstance(node,forbidden) for node in ast.walk(ast.parse(source)))
    namespace={};exec(source,namespace)
    fn=namespace['different_uint32']
    for a in (0,1,2,3,2**31,2**32-1):
        for b in (0,1,2,3,2**31,2**32-1):
            result=fn(a,b)
            assert 0<=result<4 and result!=a and result!=b
