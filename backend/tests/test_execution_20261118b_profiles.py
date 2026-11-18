"""Verify the three November 18 companion-batch runtime profiles."""
import copy
import json
from pathlib import Path
import runpy
import subprocess

import pytest

BACKEND = Path(__file__).resolve().parents[1]
FIXTURES = BACKEND / 'tests/fixtures'
AUTHOR = runpy.run_path(str(FIXTURES / 'execution_catalog_authoring.py'))
MANIFEST = json.loads((BACKEND / 'seeds/execution_cases.json').read_bytes())['questions']
INPUTS = json.loads((FIXTURES / 'execution_batch1118b_inputs.json').read_bytes())
SMOKE = json.loads((FIXTURES / 'execution_smoke.json').read_bytes())['cases']


def test_previous_profiles_are_identical_and_all_new_profiles_have_inputs():
    prior = json.loads(subprocess.check_output([
        'git', 'show', '9733b6e3eccfdb032b72f25b7d1d5b1111fc7bc2:backend/seeds/execution_cases.json',
    ], cwd=BACKEND.parent))['questions']
    assert len(prior) == 69
    assert set(MANIFEST) - set(prior) == set(INPUTS) == set(AUTHOR['BATCH1118B_SOURCES'])
    assert all(MANIFEST[key] == spec for key, spec in prior.items())


@pytest.mark.parametrize('key', sorted(INPUTS))
def test_positive_and_negative_sources_use_independent_oracles(key):
    spec = MANIFEST[key]['languages']['python']
    source = AUTHOR['batch1118b_source'](key)
    smoke, = [row for row in SMOKE if row['question_key'] == key]
    assert smoke['correct'] == source
    correct, wrong = {}, {}
    exec(compile(source,key,'exec'),correct)
    exec(compile(smoke['wrong'],key,'exec'),wrong)
    with pytest.raises(SyntaxError):
        compile(smoke['syntax_error'],key,'exec')
    rejects = []
    for given, case in zip(INPUTS[key]['languages']['python']['cases'],spec['cases'],strict=True):
        assert set(given) == {'args'} and given['args'] == case['args']
        args = given['args']
        expected = AUTHOR['ORACLES'][key](*copy.deepcopy(args))
        assert correct[spec['entry']](*copy.deepcopy(args)) == expected == case['expected']
        rejects.append(wrong[spec['entry']](*copy.deepcopy(args)) != expected)
    assert 12 <= len(rejects) <= 32 and any(rejects)
