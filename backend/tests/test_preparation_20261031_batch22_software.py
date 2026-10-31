"""Independent finite oracles and native evidence for the software intake.

The eight Python suites execute references. The native evidence is bound to
the exact C sources and harness; the native test reruns only when a local
compiler is available. Neither test type asserts ISR concurrency correctness.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / 'interview_preparation'
SCRIPT = BANK / 'checks/check_batch22_software.py'


def load_checks():
    spec = importlib.util.spec_from_file_location('batch22_software_checks', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EXPECTED = {'224': 8421, '225': 5463, '226': 14645, '228': 4,
            '229': 9842, '230': 21844, '094': 65539, '160': 9843}


@pytest.mark.parametrize('number', EXPECTED)
def test_independent_python_oracle_matches_published_finite_report(number):
    actual = load_checks().CHECKS[number]()
    suffix = '-software-batch22' if number in ('094', '160') else ''
    recorded = json.loads((BANK / f'checks/prep-{number}{suffix}-verification.json').read_bytes())
    assert actual == recorded
    assert actual['passed'] and actual['python_executed']
    assert actual['cases'] == EXPECTED[number]
    assert actual['professional_review'] == 'pending'


def test_compiled_c_evidence_matches_exact_references_and_harness():
    evidence = json.loads((BANK / 'checks/batch22-software-native-verification.json').read_bytes())
    assert evidence['passed'] and evidence['compile_exit'] == evidence['run_exit'] == 0
    assert evidence['compiler'] == 'gcc' and evidence['network_policy'] == 'deny-all'
    assert {'-std=c99', '-Wall', '-Wextra', '-Werror', '-pedantic'} <= set(evidence['flags'])
    # The captured compiler input uses Windows CRLF. Canonical LF binding is
    # portable across Git checkouts; raw compiler-input hashes are retained.
    for relative, expected_hash in evidence['canonical_lf_source_sha256'].items():
        assert hashlib.sha256((ROOT / relative).read_text('utf-8').encode()).hexdigest() == expected_hash
    harness = (BANK / 'checks/check_batch22_software_native.c').read_text('utf-8')
    for name in ('prep_230_request_fifo.c', 'prep_094_significant_bits_batch22.c',
                 'prep_160_uppercase_counting_batch22.c'):
        harness = harness.replace(f'#include "../solutions/{name}"', (BANK / 'solutions' / name).read_text('utf-8'))
    assert hashlib.sha256(harness.encode()).hexdigest() == evidence['canonical_lf_amalgamated_sha256']
    assert evidence['result'] == {'passed': True, 'fifo_traces': 21844,
                                  'reversal_cases': 65539, 'sort_cases': 9843,
                                  'assertions': 562139}


def test_native_c99_harness_when_a_local_compiler_is_available(tmp_path):
    compiler = shutil.which('gcc') or shutil.which('clang')
    if compiler is None:
        pytest.skip('No local C99 compiler; exact isolated GCC execution evidence is checked separately.')
    target = tmp_path / 'batch22-software-check.exe'
    subprocess.run([compiler, '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-pedantic',
                    str(BANK / 'checks/check_batch22_software_native.c'), '-o', str(target)],
                   check=True, capture_output=True, text=True, timeout=30)
    output = subprocess.run([str(target)], check=True, capture_output=True, text=True, timeout=30)
    result = json.loads(output.stdout)
    assert result['passed'] and result['assertions'] == 562139


def test_original_examples_and_different_width_contracts_are_distinct():
    checks = load_checks()
    significant = checks.load('prep_094_significant_bits_batch22')
    assert significant.reverse_significant(13) == 11
    assert int(f'{13:08b}'[::-1], 2) == 176
    assert significant.reverse_significant(significant.reverse_significant(8)) == 1
    compaction = checks.load('prep_229_stable_zero_compaction')
    source = [1, 0, 9, 0, 3, 4, 5, 1]
    assert compaction.move_zeroes(source) is source
    assert source == [1, 9, 3, 4, 5, 1, 0, 0]


def test_fifo_both_requests_boundary_semantics_are_not_interchangeable():
    queue_type = load_checks().load('prep_230_fifo_requests_model').RequestFifo
    empty = queue_type(1)
    assert empty.step(True, 7, True) == {'wrote': True, 'read': True, 'value': 7}
    assert empty.is_empty
    full = queue_type(1)
    assert full.step(True, 7, False)['wrote']
    assert full.step(True, 9, True) == {'wrote': False, 'read': True, 'value': 7}
    assert full.is_empty
