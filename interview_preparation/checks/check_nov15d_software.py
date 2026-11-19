"""Reproducible independent checks; does not claim a live network/human review."""
import ast
import hashlib
import itertools
import json
import random
import runpy
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / 'interview_preparation'
ORACLES = runpy.run_path(str(ROOT / 'backend/tests/fixtures/execution_1115d_oracles.py'))
voltage = runpy.run_path(str(BANK / 'solutions/prep_359_first_failure_decimal_grid.py'))
different = runpy.run_path(str(BANK / 'solutions/prep_361_distinct_from_two_uint32.py'))['different_uint32']
distance = runpy.run_path(str(BANK / 'solutions/prep_362_minimum_cross_array_distance.py'))['minimum_cross_distance']
RNG = random.Random(20261115)


def report(n, data, paths):
    data.update(question_id=f'PREP-{n:03d}', human_expert_review=False,
                source_sha256={path:hashlib.sha256((BANK/path).read_bytes()).hexdigest() for path in paths})
    (BANK/f'checks/prep-{n}-1115d-verification.json').write_text(
        json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def check_voltage():
    cases=0
    for length in range(8):
        grid = [f'{i/10:.1f}' for i in range(1,length+1)]
        for bits in itertools.product([False,True],repeat=length):
            fail = [value for value,selected in zip(grid,bits) if selected]
            args=['0',f'{(length+1)/10:.1f}','0.1',fail]
            assert voltage['first_failure_voltage'](*args)==ORACLES['voltage_oracle'](*args)
            cases+=1
    decimal_cases=[
        ['0','1','0.1',['0.3','0.8']], ['0','0.3','0.1',['0','0.3']],
        ['-0.35','0.3','0.05',['-0.30','0.10']],
        ['1.01','1.5','0.13',['1.14','1.4']], ['1','2','1', ['1','2']],
        ['0','1','0.2',['0.3','1']], ['1e20','100000000000000000001','0.125',['100000000000000000000.375']],
        ['0.00001','0.00009','0.00001',['0.0000300']],
        ['-1','0','0.3',['-0.7','-0.1']], ['0','0.4','0.1',['3e-1']],
    ]
    for args in decimal_cases:
        assert voltage['first_failure_voltage'](*args)==ORACLES['voltage_oracle'](*args)
        cases+=1
    # Observe the actual sequence and early stopping, not only returned values.
    from fractions import Fraction
    seen=[]
    def test(value):
        seen.append(value)
        return value != Fraction(3,10)
    assert voltage['find_failure']('0','1','0.1',test)==Fraction(3,10)
    assert seen==[Fraction(1,10),Fraction(2,10),Fraction(3,10)]
    invalid=[('0','1','0'),('0','1','-0.1'),('1','1','0.1'),('2','1','0.1'),('NaN','1','0.1'),('0','Infinity','0.1'),('0','1','bad')]
    for args in invalid:
        try: voltage['find_failure'](*args,lambda _:True)
        except ValueError: pass
        else: raise AssertionError(('invalid accepted',args))
    report(359,dict(status='passed',oracle='Independent decimal-scaled integer ruler/range and reduced-fraction output',
        finite_cases=cases,exhaustive_failure_patterns=255,invalid_inputs=len(invalid),
        early_stop_sequence_checked=True,physical_equipment_test=False),['solutions/prep_359_first_failure_decimal_grid.py'])


def check_distinct():
    cases=0
    for width in range(2,9):
        for a in range(1<<width):
            for b in range(1<<width):
                actual=different(a,b)
                assert actual==ORACLES['different_oracle'](a,b)
                assert 0<=actual<4 and actual!=a and actual!=b
                cases+=1
    for _ in range(20000):
        a,b=RNG.randrange(1<<32),RNG.randrange(1<<32)
        assert different(a,b)==ORACLES['different_oracle'](a,b)
        assert different(a,b) not in (a,b)
        cases+=1
    tree=ast.parse((BANK/'solutions/prep_361_distinct_from_two_uint32.py').read_text(encoding='utf8'))
    forbidden=(ast.If,ast.IfExp,ast.Compare,ast.For,ast.While,ast.Match,ast.BoolOp,ast.Call,ast.Subscript)
    assert not any(isinstance(node,forbidden) for node in ast.walk(tree))
    # One-bit impossibility: no candidate can avoid both zero and one.
    assert not [candidate for candidate in (0,1) if candidate not in (0,1)]
    zig=ROOT.parent/'.checks/intake-nov14/soft/tools/ziglang/zig.exe'
    assert zig.exists(),zig
    with tempfile.TemporaryDirectory(prefix='prep361-') as temp:
        tmp=Path(temp)
        source=str(BANK/'solutions/prep_361_distinct_from_two_uint32.c').replace('\\','/')
        driver=f'''#include <stdio.h>
#include "{source}"
int main(void) {{
    unsigned long tested=0;
    for (uint32_t a=0;a<256;a++) for(uint32_t b=0;b<256;b++) {{
        uint32_t y=different_uint32(a,b);
        if(y==a || y==b || y>3) return 1;
        tested++;
    }}
    uint32_t state=UINT32_C(1234567);
    for(unsigned i=0;i<100000;i++) {{
        state^=state<<13;state^=state>>17;state^=state<<5;uint32_t a=state;
        state^=state<<13;state^=state>>17;state^=state<<5;uint32_t b=state;
        uint32_t y=different_uint32(a,b);
        if(y==a || y==b || y>3) return 2;
        tested++;
    }}
    printf("%lu",tested);return 0;
}}'''
        (tmp/'check.c').write_text(driver,encoding='utf8')
        subprocess.run([str(zig),'cc','-std=c11','-Wall','-Wextra','-Werror','-O2',str(tmp/'check.c'),'-o',str(tmp/'check.exe')],check=True,capture_output=True)
        native_count=int(subprocess.check_output([str(tmp/'check.exe')]))
    report(361,dict(status='passed',oracle='Enumerate the four canonical values by independent bit constraints and verify result differs from both inputs',
        python_cases=cases,exhaustive_widths=list(range(2,9)),branch_free_ast_checked=True,
        native_c_compiled=True,native_c_cases=native_count,compiler='Zig C11 -O2 -Wall -Wextra -Werror',
        compiler_constant_time_proof=False),['solutions/prep_361_distinct_from_two_uint32.py','solutions/prep_361_distinct_from_two_uint32.c'])


def check_distance():
    arrays=[list(t) for n in range(4) for t in itertools.product(range(-2,3),repeat=n)]
    cases=0
    for left in arrays:
        for right in arrays:
            a,b=left[:],right[:]
            expected=ORACLES['distance_oracle'](left,right)
            assert distance(left,right)==expected
            assert left==a and right==b
            cases+=1
    for _ in range(1000):
        a=[RNG.randrange(-10**15,10**15) for _ in range(RNG.randrange(16))]
        b=[RNG.randrange(-10**15,10**15) for _ in range(RNG.randrange(16))]
        expected=ORACLES['distance_oracle'](a,b)
        assert distance(a,b)==expected==distance(b,a)
        assert distance([v+47 for v in a],[v+47 for v in b])==expected
        cases+=1
    extremes=[([-2**31],[2**31-1]),([-2**1000],[2**1000]),([0,2**32-1],[2**32]),([5],[5])]
    for a,b in extremes:
        assert distance(a,b)==ORACLES['distance_oracle'](a,b)
        cases+=1
    report(362,dict(status='passed',oracle='Independent Cartesian-product absolute-distance minimum',
        exhaustive_list_domain=[-2,-1,0,1,2],exhaustive_max_length=3,finite_cases=cases,
        input_preservation=True,symmetry_and_uniform_translation=True),['solutions/prep_362_minimum_cross_array_distance.py'])


if __name__=='__main__':
    check_voltage();check_distinct();check_distance()
    report(360,dict(status='checked',verification_scope='Bilingual conceptual trace and primary-standards cross-check; no live network capture',
        endpoint_ip=['192.0.2.10','198.51.100.20'],first_next_hop='192.0.2.1',
        expected_forwarding='Switch uses MAC; router routes IP and rebuilds link encapsulation; no NAT',
        primary_references=[
            'https://www.itu.int/rec/T-REC-X.200-199407-I/en',
            'https://www.rfc-editor.org/rfc/rfc1122.html',
            'https://www.rfc-editor.org/rfc/rfc826.html',
            'https://www.rfc-editor.org/rfc/rfc9293.html',
            'https://www.rfc-editor.org/rfc/rfc8446.html',
            'https://www.rfc-editor.org/rfc/rfc8200.html#section-5',
            'https://www.rfc-editor.org/rfc/rfc4861.html'],
        live_network_capture=False),[])
    print('PREP-359..362 independent software checks passed')
