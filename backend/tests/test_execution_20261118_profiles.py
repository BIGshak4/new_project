"""Coverage for the new scoped array, rolling rank, and tree runner contracts."""
import json
from pathlib import Path
import runpy
import subprocess


BACKEND = Path(__file__).resolve().parents[1]
FIXTURES = BACKEND / 'tests/fixtures'
MANIFEST_PATH = 'backend/seeds/execution_cases.json'


def test_previous_profiles_remain_identical_and_new_contracts_are_covered():
    prior = json.loads(subprocess.check_output([
        'git', 'show', '99e6cb9f65a726293637ec2549a74ba982aee321:' + MANIFEST_PATH,
    ], cwd=BACKEND.parent))['questions']
    manifest = json.loads((BACKEND / 'seeds/execution_cases.json').read_bytes())['questions']
    authored = runpy.run_path(str(FIXTURES / 'execution_catalog_authoring.py'))
    added = authored['build_batch1118_contracts']()
    assert len(prior) == 66
    assert set(manifest) - set(prior) == set(added)
    assert all(manifest[key] == spec for key, spec in prior.items())
    for key, spec in added.items():
        assert spec['languages'] == manifest[key]['languages']
        for language, contract in spec['contract'].items():
            assert manifest[key]['contract'][language].startswith(contract)
        assert len(spec['languages']['python']['cases']) >= 12
