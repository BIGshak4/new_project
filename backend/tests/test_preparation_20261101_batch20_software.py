"""Finite independent software oracles and exact strict-native evidence."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / 'interview_preparation'


def checks():
    path = BANK / 'checks/check_intake20261101_software.py'
    spec = importlib.util.spec_from_file_location('intake1101_software_checks', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('number', ['237', '238', '239', '027', '023', '117', '151'])
def test_independent_finite_oracles_reproduce_declared_verification(number):
    actual = checks().CHECKS[number]()
    actual.update(professional_review='pending', ai_assisted=True)
    suffix = '-batch1101' if int(number) < 237 else ''
    recorded = json.loads((BANK / f'checks/prep-{number}{suffix}-verification.json').read_bytes())
    assert actual == recorded
    assert actual['passed']


def test_native_evidence_binds_exact_sources_and_compiler_input():
    evidence = json.loads((BANK / 'checks/batch1101-software-native-verification.json').read_bytes())
    assert evidence['passed'] and evidence['compiler'] == 'gcc'
    assert evidence['compile_exit'] == evidence['run_exit'] == 0
    assert evidence['network_policy'] == 'deny-all' and evidence['stopped'] and not evidence['persistent']
    assert {'-std=c99', '-Wall', '-Wextra', '-Werror', '-pedantic'} <= set(evidence['flags'])
    for path, digest in evidence['canonical_lf_source_sha256'].items():
        assert hashlib.sha256((ROOT / path).read_text('utf-8').encode()).hexdigest() == digest
    text = (BANK / 'checks/check_intake20261101_software_native.c').read_text('utf-8')
    for name in ['prep_237_dictionary.c', 'prep_238_reverse_linked_list.c', 'prep_117_int_arena_batch1101.c']:
        source = (BANK / 'solutions' / name).read_text('utf-8')
        if name == 'prep_237_dictionary.c':
            source = source.replace('#include "prep_237_dictionary.h"', (BANK / 'solutions/prep_237_dictionary.h').read_text('utf-8'))
        text = text.replace(f'#include "../solutions/{name}"', source)
    assert hashlib.sha256(text.encode()).hexdigest() == evidence['canonical_lf_amalgamated_sha256']
    assert evidence['result'] == {'passed': True, 'dictionary_histories': 66430, 'reversal_cases': 511,
                                  'arena_steps': 36000, 'assertions': 2454609, 'live_blocks': 0}


def test_native_reexecution_if_a_local_c99_compiler_is_available(tmp_path):
    compiler = shutil.which('gcc') or shutil.which('clang')
    if compiler is None:
        pytest.skip('No local C99 compiler; exact strict isolated GCC execution evidence is verified separately.')
    program = tmp_path / 'software1101.exe'
    subprocess.run([compiler, '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-pedantic',
                    str(BANK / 'checks/check_intake20261101_software_native.c'), '-o', str(program)],
                   check=True, capture_output=True, timeout=30)
    process = subprocess.run([str(program)], check=True, capture_output=True, timeout=30)
    assert json.loads(process.stdout)['assertions'] == 2454609


def test_csv_file_wrapper_preserves_embedded_line_endings_and_chunk_boundaries(tmp_path):
    module = checks().load('prep_239_streaming_csv')
    path = tmp_path / 'quoted.csv'
    path.write_bytes(b'name,value\r\n"a\r\nb","c""d"\r\nlast,')
    assert list(module.read_csv_file(path, chunk_size=1)) == [
        ['name', 'value'], ['a\r\nb', 'c"d'], ['last', '']]
    with pytest.raises(ValueError):
        list(module.read_csv_file(path, chunk_size=0))
    syntax = ast.parse((BANK / 'solutions/prep_239_streaming_csv.py').read_text('utf-8'))
    assert not any(isinstance(node, ast.Import) and any(alias.name == 'csv' for alias in node.names)
                   or isinstance(node, ast.ImportFrom) and node.module == 'csv' for node in ast.walk(syntax))


def test_variant_boundaries_are_explicit_and_not_silently_conflated():
    modules = checks()
    power = modules.load('prep_023_power_exponent_batch1101')
    assert power.power_exponent(1) == [True, 0]
    assert power.power_exponent(0) == [False, None]
    for value in [-1, 1 << 32, True, 2.0]:
        with pytest.raises(ValueError):
            power.power_exponent(value)
    packed = modules.load('prep_151_packed_array_popcount_batch1101')
    assert packed.count_packed_ones(bytes([255]), 3) == 3
    assert packed.count_packed_ones(bytes([255]), 0) == 0
    with pytest.raises(ValueError):
        packed.count_packed_ones(bytes([255]), 9)
    assert (2 * 1024**3 * 8).bit_length() == 35  # Counter for explicit 2 GiB bytes, not ambiguous source 2gb.
