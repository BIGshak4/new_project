"""Independent bounded oracles; native RTL execution is recorded separately."""
import hashlib
import importlib.util
import itertools
import json
from fractions import Fraction as F
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]


def load(number, stem):
    path=BANK/'solutions'/f'prep_{number:03d}_{stem}_1107n30.py'
    spec=importlib.util.spec_from_file_location(f'm{number}',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    cube=load(290,'cube_resistance')
    bridge=load(294,'bridge_balance')
    op=load(297,'noninverting_gain')
    sine=load(299,'sine_model')
    for resistance in [F(1,7),F(1,2),F(1),F(3),F(100)]:
        equivalent,voltage=cube.cube_resistance(resistance)
        assert equivalent==5*resistance/6
        assert all(voltage[v]==F(3,5) for v in (1,2,4))
        assert all(voltage[v]==F(2,5) for v in (3,5,6))
        for v in range(1,7):
            assert sum((voltage[v]-voltage[v^mask])/resistance for mask in (1,2,4))==0
    bridge_cases=0
    for r1,r2,r3,r4,r5 in itertools.product(range(1,5),repeat=5):
        for source in (F(-2),F(1),F(7,3)):
            left,right,current=bridge.bridge(r1,r2,r3,r4,r5,source)
            assert (current==0)==(r1*r4==r2*r3)
            assert (left-source)/r1+left/r2+current==0
            assert (right-source)/r3+right/r4-current==0
            if current==0:
                assert left==source*F(r2,r1+r2)
                assert right==source*F(r4,r3+r4)
            bridge_cases+=1
    assert bridge.bridge(1,2,3,4,5,0)[2]==0
    op_cases=0
    for rg,rf in itertools.product(range(1,9),repeat=2):
        assert op.closed_loop_gain(rg,rf)==1+F(rf,rg)
        for gain in (1,10,1000,1000000):
            g=op.closed_loop_gain(rg,rf,gain)
            assert g==gain*(1-g*F(rg,rg+rf))
            assert 0<g<op.closed_loop_gain(rg,rf)
            op_cases+=1
    assert op.closed_loop_gain(100,100)==2
    table=sine.full_table()
    assert table==[0,19260,31163,31163,19260,0,-19260,-31163,-31163,-19260]
    assert all(table[n]==sine.half_sample(n)==sine.quarter_sample(n) for n in range(10))
    assert len({abs(v) for v in table})==3
    def fa(a,b,c):
        return a^b^c,int(a+b+c>=2)
    for x in range(256):
        b=[(x>>i)&1 for i in range(8)]
        s0,c0=fa(*b[:3]);s1,c1=fa(*b[3:6]);s2,c2=fa(s0,s1,b[6]);y0,c3=fa(s2,b[7],0)
        t0,u0=fa(c0,c1,c2);y1,u1=fa(t0,c3,0);y2,y3=fa(u0,u1,0)
        assert y0+2*y1+4*y2+8*y3==x.bit_count()
    for x in range(1024):
        three=(x<<1)+x
        result=(three<<4)+x
        assert three<4096 and result<65536 and result==49*x
    for a,b in itertools.product(range(16),repeat=2):
        out=0;carry=0
        for bit in range(4):
            total=((a>>bit)&1)+((b>>bit)&1)+carry
            out|=(total&1)<<bit
            carry=total>>1
        assert out+(carry<<4)==a+b
    for a,b in itertools.product((0,1),repeat=2):
        up=(not a) or (not b);down=bool(a and b)
        assert up != down and int(up)==1-(a&b)
    files=sorted((BANK/'solutions').glob('*1107n30.*'))+[Path(__file__).resolve(),BANK/'checks/tb_hardware_1107n30.sv']
    report={'status':'pass','scope':'Python logical/exact-rational models only; native compilation/simulation is separate; no SPICE, synthesis or STA.',
            'cases':{'cube_resistance_scales':5,'bridge_nonzero_dc_cases':bridge_cases,'bridge_zero_excitation_counterexample':1,
                     'opamp_finite_gain_cases':op_cases,'opamp_ideal_resistor_pairs':64,'sine_phases':10,
                     'popcount_inputs':256,'times49_inputs':1024,'adder_pairs':256,'nand_truth_rows':4},
            'sha256':{str(p.relative_to(BANK)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    path=BANK/'checks/night1107n30-hardware-model-verification.json'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['cases']))


if __name__=='__main__':main()
