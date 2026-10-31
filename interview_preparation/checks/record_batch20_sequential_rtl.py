"""Record the actual bounded remote compiler/simulator evidence per question.

The service supplies no built-in oracle (passed=null); our self-checking
testbench executes fatal assertions and prints explicit per-family PASS lines.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'interview_preparation'
EVIDENCE = ROOT / '.impeccable/execution-intake-20261031-batch20/sequential-rtl-bounded-execution.json'
raw = json.loads(EVIDENCE.read_text(encoding='utf-8'))
assert raw['status'] == 'completed' and raw['compiled'] is True and raw['executed'] is True
assert not raw['stderr'] and not raw['compile_output']
assert 'ALL BATCH20 SEQUENTIAL RTL CHECKS PASSED' in raw['stdout']
rtl = 'solutions/prep_216_220_sequential.sv'
tb = 'solutions/prep_216_220_sequential_tb.sv'
counts = {
    'PREP-216': {'edges': 128, 'reset_phases': 4},
    'PREP-217': {'binary_streams_lengths_0_through_8': 511, 'prefix_checks': 3586, 'explicit_overlap_positions': [6, 9]},
    'PREP-218': {'accepted_64_bit_samples': 512, 'single_and_pair_modes': True, 'idle_enrollment_reset': True},
    'PREP-219': {'six_operand_width8_expressions': 256, 'idle_grammar_reset_precedence': True},
    'PREP-220': {'exhaustive_width1_preedge_transitions': 16384},
    'PREP-036': {'binary_streams_lengths_0_through_8': 511, 'numeric_invariant_prefix_checks': 3586},
}
for qid, coverage in counts.items():
    line = next(line for line in raw['stdout'].splitlines() if line.startswith(qid + ' PASS '))
    path = BASE / 'checks' / f'{qid.lower()}-batch20-verification.json'
    result = json.loads(path.read_text(encoding='utf-8'))
    result.update(hdl_compiled=True, hdl_simulated=True, hdl_self_checks_passed=True)
    result['rtl_verification'] = {
        'recorded_on': '2026-10-31', 'language': 'SystemVerilog',
        'compiled': True, 'executed': True, 'self_check_passed': True,
        'scope': 'Bounded RTL simulation; distinct from the larger Python exhaustive ranges',
        'coverage': coverage, 'pass_line': line,
        'rtl_source': rtl, 'rtl_source_sha256': hashlib.sha256((BASE / rtl).read_bytes()).hexdigest(),
        'self_contained_testbench': tb, 'testbench_sha256': hashlib.sha256((BASE / tb).read_bytes()).hexdigest(),
        'combined_simulation_runtime_ms': raw['runtime_ms'],
        'raw_execution_evidence': EVIDENCE.relative_to(ROOT).as_posix(),
        'raw_service_passed': raw['passed'],
        'assessment': 'Service has no automated oracle; success is established by all in-testbench fatal assertions completing and explicit PASS markers.',
        'earlier_larger_testbench_timeout': '.impeccable/execution-intake-20261031-batch20/sequential-rtl-execution.json',
        'physical_hardware_tested': False, 'synthesis_timing_power_verified': False,
    }
    path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print('Recorded bounded RTL evidence for six question IDs; retained Python coverage and earlier timeout evidence')
