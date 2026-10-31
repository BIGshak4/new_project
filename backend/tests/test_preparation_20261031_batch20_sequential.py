"""Bounded exhaustive independent-oracle checks for new sequential questions."""
import importlib.util
import unittest
from pathlib import Path


class Batch20SequentialTests(unittest.TestCase):
    def test_finite_models_against_independent_oracles(self):
        root = Path(__file__).resolve().parents[2]
        script = root / 'interview_preparation/checks/check_20261031_batch20_sequential.py'
        spec = importlib.util.spec_from_file_location('check_batch20_seq', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        results = module.run(write=False)
        self.assertEqual(set(results), {'PREP-036', 'PREP-216', 'PREP-217', 'PREP-218', 'PREP-219', 'PREP-220'})
        self.assertEqual(results['PREP-220']['exhaustive_width1_preedge_transitions'], 16384)


if __name__ == '__main__':
    unittest.main()
