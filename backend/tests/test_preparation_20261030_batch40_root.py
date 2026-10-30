"""Independent functional checks for root-authored October30 second intake."""
import importlib.util
from pathlib import Path

import pytest

CHECKS = Path(__file__).resolve().parents[2]/'interview_preparation/checks'


@pytest.mark.parametrize('name',['155','156','157','009_sorter_variant'])
def test_model_against_independent_oracle(name):
    path = CHECKS/f'check_prep_{name}.py'
    spec = importlib.util.spec_from_file_location('batch40_'+name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.verify()['status'] == 'passed'
