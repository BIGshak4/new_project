"""New private test inputs preserve old profiles and use independent semantic oracles."""
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
INPUTS=json.loads((F/'execution_batch1115b_inputs.json').read_bytes())
MANIFEST=json.loads((BACKEND/'seeds/execution_cases.json').read_bytes())['questions']


@pytest.mark.parametrize('key', sorted(INPUTS))
def test_input_only_cases_use_independent_oracles(key):
    given=INPUTS[key]['languages']['python']
    built=MANIFEST[key]['languages']['python']
    assert len(given['cases'])==len(built['cases'])==12
    namespace={}
    exec(compile(AUTHOR['batch1115b_source'](key),key,'exec'),namespace)
    reference=namespace[built['entry']]
    for source,case in zip(given['cases'],built['cases'],strict=True):
        assert set(source)=={'args'} and source['args']==case['args']
        expected=AUTHOR['ORACLES'][key](*copy.deepcopy(source['args']))
        assert expected==case['expected']==reference(*copy.deepcopy(case['args']))


def test_prior_profiles_remain_identical_and_new_turnback_has_no_heading_requirement():
    prior=json.loads(subprocess.check_output(['git','show','ca0db56:backend/seeds/execution_cases.json'],cwd=ROOT))['questions']
    assert len(prior)==56 and len(MANIFEST)==63
    assert all(MANIFEST[key]==spec for key,spec in prior.items())
    spec=MANIFEST['prep-turtle-single-sequence-return-position']['languages']['python']
    examples={tuple(c['args']):c['expected'] for c in spec['cases']}
    assert examples['T',] is True and examples['MTM',] is True
    assert examples['MMTM',] is False


def test_node_operation_preserves_target_identity_and_detaches_successor():
    namespace={}
    exec(AUTHOR['batch1115b_source']('prep-delete-given-interior-list-node'),namespace)
    Node=namespace['Node']
    tail=Node(3)
    successor=Node(2,tail)
    target=Node(1,successor)
    head=Node(0,target)
    namespace['delete_given'](target)
    assert head.next is target and target.value==2 and target.next is tail
    with pytest.raises(ValueError):namespace['delete_given'](tail)
