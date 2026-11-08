"""Independent finite models and physical observation limits; no STA/SPICE."""
import hashlib
import importlib.util
import itertools
import json
import math
from fractions import Fraction as F
from pathlib import Path
from random import Random

BANK=Path(__file__).resolve().parents[1]


def load(stem):
    path=BANK/'solutions'/f'{stem}_1108b20.py'
    spec=importlib.util.spec_from_file_location(stem,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def main():
    pvt=load('prep_306_pvt_slack');rc=load('prep_307_rc_threshold')
    ground=load('prep_132_ground_coupling');adc=load('prep_310_adc_schedule')
    wood=load('prep_053_wood_model');sine=load('prep_299_sine32_model')
    counts={}
    checks=0
    for c,period,skew,uncertainty in itertools.product(pvt.TEACHING_CORNERS.values(),[F('.9'),F(1),F('1.1')],[F('-.05'),F(0),F('.05')],[F(0),F('.02'),F('.05')]):
        setup,hold=pvt.slack(c,period,skew,setup_uncertainty=uncertainty,hold_uncertainty=uncertainty)
        latest=c['cq_max']+c['logic_max'];deadline=period+skew-F('.08')-uncertainty
        earliest=c['cq_min']+c['logic_min'];keep_until=skew+F('.06')+uncertainty
        assert setup==deadline-latest and hold==earliest-keep_until;checks+=1
    ss=pvt.slack(pvt.TEACHING_CORNERS['SS_lowV_hot'])
    ff=pvt.slack(pvt.TEACHING_CORNERS['FF_highV_cold'])
    assert ss==(F('-.05'),F('.27')) and ff==(F('.47'),F('-.03'))
    counts['pvt_arrival_budget_cases']=checks
    checks=0
    for vs,r,tau in itertools.product([F(1),F('3.3'),F(5)],[1,10,1000],[1e-6,.001,1.]):
        reference=rc.divider(vs,r,2*r);assert reference==2*vs/3
        assert rc.comparator(reference,reference)==0
        assert rc.comparator(reference-F(1,1000000),reference)==0
        assert rc.comparator(reference+F(1,1000000),reference)==1
        cross=rc.charging_crossing(tau)
        assert math.isclose(rc.capacitor_voltage(float(vs),tau,cross),float(reference),rel_tol=1e-12)
        assert rc.capacitor_voltage(float(vs),tau,cross-.01*tau)<reference
        assert rc.capacitor_voltage(float(vs),tau,cross+.01*tau)>reference
        # Independent forward-Euler integration of the charge ODE to one tau.
        value=0.;dt=tau/10000
        for _ in range(10000):value+=(float(vs)-value)*dt/tau
        assert abs(value-rc.capacitor_voltage(float(vs),tau,tau))<float(vs)*2e-5
        checks+=1
    counts['single_threshold_rc_cases']=checks
    checks=0
    for vdd,vm_fraction,tau in itertools.product([1.,3.3,5.],[.2,.5,.8],[1e-6,.001,1.]):
        vm=vdd*vm_fraction;cross=ground.first_pulse_width(vdd,vm,tau)
        assert math.isclose(ground.relax_ground(vdd,cross,tau),vm,rel_tol=1e-12)
        assert ground.relax_ground(vdd,cross-.01*tau,tau)>vm
        assert ground.relax_ground(vdd,cross+.01*tau,tau)<vm
        before=ground.relax_ground(vdd,tau,tau)
        after=ground.edge_node(before,vdd,0)
        assert after<0 and math.isclose(vdd-before,0-after)
        checks+=1
    counts['ground_coupled_edge_cases']=checks
    assert adc.per_channel_rate(1000000)==250000
    assert adc.per_channel_rate(800000)==200000
    schedule=adc.round_robin(slots=100)
    for channel in range(4):
        times=[t for c,t in schedule if c==channel]
        assert len(times)==25 and all(b-a==F(4,1000000) for a,b in itertools.pairwise(times))
    assert adc.slot_fits(F(1,10000000),F(3,10000000),F(5,10000000),1000000)
    assert not adc.slot_fits(F(2,10000000),F(4,10000000),F(5,10000000),1000000)
    assert math.isclose(adc.settling_time(1.,1.,1/8192),13*math.log(2))
    for n in range(32):
        assert abs(math.sin(2*math.pi*100000*n/200000))<1e-12
        assert math.isclose(math.cos(2*math.pi*150000*n/250000),math.cos(2*math.pi*100000*n/250000),abs_tol=1e-12)
    counts['adc_schedule_slots']=100;counts['adc_alias_samples']=32
    # Geometry supplies an independent completion oracle for monotone passages.
    observations=0
    for short,to_right,pauses in itertools.product([False,True],[False,True],range(5)):
        length=2 if short else 6;start=-length-1 if to_right else 5;end=5 if to_right else -length-1
        increment=1 if to_right else -1;state=0
        for position in range(start+increment,end+increment,increment):
            for hold in range(pauses+1):
                state,right,left=wood.step(state,wood.sensors(position,length),short)
                assert right==bool(to_right and position==end and hold==0)
                assert left==bool(not to_right and position==end and hold==0)
                observations+=1
    # Long-object walks may reverse; boundaries independently determine completion.
    for from_left,seed in itertools.product([False,True],range(64)):
        length=6;position=-7 if from_left else 5;state=0;rng=Random(seed)
        for _ in range(300):
            position=max(-7,min(5,position+rng.choice([-1,0,1])))
            state,right,left=wood.step(state,wood.sensors(position,length),False)
            assert right==bool(from_left and position==5)
            assert left==bool(not from_left and position==-7)
            observations+=1
            if right or left:break
    # Equal observations, different physical destinations: short reversal is unobservable.
    cross=[-3,-2,-1,0,1,2,3,4,5];retreat=[-3,-2,-1,0,1,2,3,2,1]
    assert [wood.sensors(p,2) for p in cross]==[wood.sensors(p,2) for p in retreat]
    assert cross[-1]>4 and 0<retreat[-1]<2
    counts['wood_geometric_observations']=observations;counts['short_reversal_indistinguishable_pair']=1
    table=sine.full_table();assert table==[sine.sample(n) for n in range(32)]
    assert len({abs(v) for v in table})==9
    assert all(table[(n+16)%32]==-table[n] for n in range(16))
    assert table[0]==table[16]==0 and table[8]==32767 and table[24]==-32767
    counts['sine32_phases']=32
    for a,b in itertools.product(range(256),repeat=2):
        swap=a<b;hi=b if swap else a;lo=a if swap else b
        assert hi==max(a,b) and lo==min(a,b) and hi+lo==a+b
    counts['minmax8_pairs']=65536
    files=sorted((BANK/'solutions').glob('*1108b20.*'))+[Path(__file__).resolve(),BANK/'checks/tb_hardware_1108b20.sv']
    result={'status':'pass','scope':'Python exact/numerical/geometry models; independent physical oracles and bounded coverage. Native SV evidence is separate; no SPICE, PDK characterization, physical ADC or STA signoff.',
            'counts':counts,'sha256':{str(p.relative_to(BANK)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    out=BANK/'checks/batch1108b20-hardware-model-verification.json'
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(counts))


if __name__=='__main__':main()
