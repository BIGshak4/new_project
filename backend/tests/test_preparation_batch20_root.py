"""Independent executable checks for the new fixed-width allocator and one-hot variant."""
import importlib.util
from pathlib import Path

import pytest

BANK = Path(__file__).resolve().parents[2] / 'interview_preparation'


@pytest.mark.parametrize('number', [102, 105])
def test_actual_authored_models_against_independent_oracles(number):
    spec = importlib.util.spec_from_file_location(f'verify{number}', BANK / f'checks/check_prep_{number}.py')
    check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check)
    assert check.verify()['passed']
