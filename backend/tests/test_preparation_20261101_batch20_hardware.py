"""Equation/history oracles plus exact-source native RTL execution evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/'interview_preparation/checks/check_batch1101_hardware.py'
spec=importlib.util.spec_from_file_location('independent_batch1101_hw_checks',SCRIPT)
CHECKS=importlib.util.module_from_spec(spec)
spec.loader.exec_module(CHECKS)


@pytest.mark.parametrize('number,cases',[(233,110),(234,64),(235,2051),(236,2120),(91,9841)])
def test_finite_independent_oracles_match_recorded_coverage(number,cases):
    actual=CHECKS.CHECKS[number]()
    assert actual['passed'] and actual['cases']==cases
    name=f'prep-{number:03d}-verification.json' if number!=91 else 'prep-091-polarity-batch1101-verification.json'
    assert actual==json.loads((SCRIPT.parent/name).read_bytes())


def test_dc_return_path_and_steady_state_capacitor_counterexample():
    m=CHECKS.load('prep_233_ir_drop')
    dc=m.dc_rail(1,2,.015,.005)
    assert dc['load_voltage']==pytest.approx(.96)
    assert dc['loss_watts']==pytest.approx(.08)
    assert m.dc_rail(1,2,0,.02)['load_voltage']==pytest.approx(.96)
    # No capacitor value enters the steady-state DC equation. Two identical
    # return paths halve only the return contribution, not both contributions.
    assert m.dc_rail(1,2,.015,.0025)['drop']==pytest.approx(.035)
    assert m.ideal_reservoir_capacitance(0,1,.1)==0
    with pytest.raises(ValueError):
        m.allowed_resistance(.01,0)


def test_mode00_is_any_zero_and_mode01_is_a_strict_majority():
    m=CHECKS.load('prep_234_controlled_predicates')
    assert [m.controlled(0,mode) for mode in range(4)]==[1,0,0,1]
    assert [m.controlled(15,mode) for mode in range(4)]==[0,1,0,1]
    assert m.controlled(3,1)==0
    assert m.controlled(7,1)==1
    # Population parity differs from the numerical even/odd LSB test.
    assert m.controlled(3,2)==0 and (3&1)==1


def test_live_detector_does_not_latch_every_event_or_wait_for_clock():
    m=CHECKS.load('prep_091_polarity_batch1101')
    assert m.edge_events([('data',1),('data',0),('clock',None)])==[[1,0,1],[0,0,0],[0,0,0]]
    assert m.edge_events([('data',1),('clock',None),('data',0)])[-1]==[0,1,1]


def test_rtl_evidence_binds_exact_sources_and_exhaustive_testbench():
    e=json.loads((SCRIPT.parent/'batch1101-hardware-native-verification.json').read_bytes())
    assert e['passed'] and e['compile_exit']==e['run_exit']==0
    assert e['network_policy']=='deny-all' and e['stopped'] and not e['persistent']
    assert e['compile_args'][0]=='iverilog' and '-g2012' in e['compile_args']
    assert e['compile_stderr']==''
    for path,digest in e['canonical_lf_source_sha256'].items():
        assert hashlib.sha256((ROOT/path).read_text(encoding='utf-8').encode()).hexdigest()==digest
    assert 'PASS batch20 hardware checks=1054857' in e['stdout']
    assert e['coverage']['decoderN4']==65536*16
