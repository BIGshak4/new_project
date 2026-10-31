"""Executable oracle regressions for three newly authored software questions."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

BANK = Path(__file__).resolve().parents[2] / 'interview_preparation'
CHECKS = BANK / 'checks'


def load_checks():
    spec = importlib.util.spec_from_file_location(
        'batch20_algorithms_checks', CHECKS / 'check_batch20_algorithms_20261031.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('ident', ['PREP-210', 'PREP-211'])
def test_python_algorithms_match_independent_oracles_and_persisted_reports(ident):
    result = load_checks().CHECKS[ident]()
    assert result['passed'] and result['professional_review'] == 'pending'
    assert result == json.loads((CHECKS / (ident.lower() + '-verification.json')).read_bytes())


def test_c_adt_compiles_and_runs_ownership_and_failure_injection_harness(tmp_path):
    compiler = shutil.which('cc') or shutil.which('gcc') or shutil.which('clang')
    if compiler is None:
        pytest.skip('No local C compiler: C execution evidence is the separately persisted isolated-run report')
    executable = tmp_path / ('prep212.exe' if __import__('os').name == 'nt' else 'prep212')
    command = [compiler, '-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic',
               str(CHECKS / 'prep_212_linked_list_adt_test.c'), '-o', str(executable)]
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
    completed = subprocess.run([str(executable)], check=True, capture_output=True, text=True, timeout=30)
    result = json.loads(completed.stdout)
    assert result['passed'] and result['allocation_failure_injected']
    assert result['insertion_scenarios'] == 54 and result['live_blocks_at_exit'] == 0


def test_opaque_c_public_boundary_declares_lifetime_and_observation_api():
    header = (BANK / 'solutions/prep_212_linked_list_adt.h').read_text('utf-8')
    assert 'typedef struct List List;' in header and 'typedef struct Node Node;' in header
    assert 'struct Node {' not in header and 'struct List {' not in header
    assert all(name in header for name in ('listInit', 'listDestroy', 'createNode',
                                          'listContains', 'insertNode', 'destroyDetachedNode'))
    assert (CHECKS / 'prep_212_linked_list_adt_amalgamated.c').read_text('utf-8') == load_checks().amalgamate_c_harness()
    report = json.loads((CHECKS / 'prep-212-verification.json').read_bytes())
    assert report['professional_review'] == 'pending'
    if report.get('c_compiled'):
        assert report['c_executed'] and report['platform_assessment_passed'] is None
        assert report['execution_result']['passed']
        assert report['execution_result']['allocation_failure_injected']
        assert report['execution_result']['insertion_scenarios'] == 54
        assert report['execution_result']['assertions'] == 2264
        assert report['execution_result']['live_blocks_at_exit'] == 0
        for relative, expected in report['source_sha256'].items():
            assert hashlib.sha256((BANK / relative).read_bytes()).hexdigest() == expected
