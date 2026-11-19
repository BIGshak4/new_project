"""Finite logical oracles for the November 15 hardware questions.

This suite exercises Python models. It does not claim HDL synthesis or physical
timing, metastability, retention, drive-strength or charge verification.
"""
from itertools import combinations, product, permutations
from pathlib import Path
import json,random,runpy

BANK=Path(__file__).resolve().parents[1]
def model(number):
    return runpy.run_path(str(BANK/f'solutions/prep_{number:03}_hardware1115.py'))

results={}
m=model(338)
table=(1,2,3,4,5,1,1,1)
for state,expected in enumerate(table):
    assert m['step'](state)==expected
    assert m['step'](state,True)==1
    assert m['load_decode'](state)==int(state in (5,6,7))
for q in range(1,6):assert m['reduced_legal_cycle_decode'](q)==int(q==5)
results['PREP-338']=dict(complete_states=8,reset_checks=8,decoder_checks=8,legal_dontcare_checks=5)

m=model(339)
cycle=((0,0,1),(1,0,0),(0,1,0),(1,0,1),(1,1,0),(1,1,1),(0,1,1))
rows=m['trace'](70)
for edge,state,y in rows:
    assert state==cycle[edge%7] and y==cycle[edge%7][2]
assert len({m['step'](s) for s in product((0,1),repeat=3)})==8
assert m['step']((0,0,0))==(0,0,0)
results['PREP-339']=dict(all_states=8,trace_samples=71,nonzero_period=7)

m=model(340);histograms=0
for n0 in range(17):
    for n1 in range(17-n0):
        for n2 in range(17-n0-n1):
            n3=16-n0-n1-n2
            values=[0]*n0+[1]*n1+[2]*n2+[3]*n3
            assert m['maximum16'](values)==max(values)
            histograms+=1
positions=0
for a,b in product(range(4),repeat=2):
    for i,j in product(range(16),repeat=2):
        words=[0]*16;words[i]=a;words[j]=b
        assert m['maximum16'](words)==max(words)
        positions+=1
rng=random.Random(1115)
for _ in range(1000):
    words=[rng.randrange(4) for _ in range(16)]
    assert m['maximum16'](words)==max(words)
assert histograms==969
results['PREP-340']=dict(all_value_histograms=histograms,position_checks=positions,deterministic_random_checks=1000,coverage_basis='Every count vector plus position checks; the equation is symmetric under word permutation.')

m=model(341)
vocabulary=[''.join(word) for size in range(1,4) for word in product('ab',repeat=size)]
texts=['\n','   \n',' '.join(vocabulary)+'\n','ab a ab bba\n']
for size in range(1,4):
    for indices in product(range(14),repeat=size):
        words=[vocabulary[i] for i in indices]
        texts.append('  '+'  '.join(words)+'   \n')
for text in texts:
    expected=len(set(text.split()))
    assert m['count_distinct'](text)==expected
    unit=m['DistinctWords']()
    for ch in text:
        before=unit.__dict__.copy();unit.accept('x',False);assert unit.__dict__==before
        unit.accept(ch)
    before=unit.__dict__.copy();unit.accept('a');assert unit.__dict__==before
    unit.reset();assert unit.count==unit.seen==unit.length==0 and not unit.done
for invalid in ('aaaa\n','x\n','abab\n','aba bbb x\n','a b','a\nb','a\n\n'):
    try:m['count_distinct'](invalid)
    except ValueError:pass
    else:raise AssertionError(invalid)
results['PREP-341']=dict(valid_streams=len(texts),invalid_streams=7,word_universe=14,stalls_and_reset_checked=True)

m=model(342)
for a,b,n,y in product((0,1),repeat=4):
    nn,yy,en=m['settle'](a,b,n,y)
    assert nn==(b if a==0 else n)
    expected=y if a==0 or b==y else n
    assert yy==expected and en==int(bool(a and b!=yy))
    assert m['settle'](a,b,nn,yy)==(nn,yy,en)
for previous,b in product((0,1),repeat=2):
    n,y,_=m['settle'](0,b,0,previous)
    n,y,_=m['settle'](1,b,n,y);assert y==b
    n,y,_=m['settle'](1,1-b,n,y);assert y==b
results['PREP-342']=dict(retained_state_combinations=16,valid_acquisition_traces=4,physical_charge_verified=False)

m=model(216);traces=0
for active in range(3):
    for request_sequence in product(range(3),repeat=8):
        q=0;s=active
        for requested in request_sequence:
            q=m['rising'](q)
            before=m['output'](q,s)
            new=m['falling'](q,s,requested)
            after=m['output'](q,new)
            assert before==after
            if new!=s:assert q==0
            s=new
        traces+=1
for q in range(8):assert m['rising'](q)==(q+1)%8
for tap in range(3):
    samples=[m['output'](edge%8,tap) for edge in range(32)]
    assert samples==[(edge//(1<<tap))%2 for edge in range(32)]
results['PREP-216']=dict(selector_request_traces=traces,trace_source_cycles=8,all_counter_states=8,selector_updates_preserve_output=True)

m=model(30)
for values in product((-1,0,1,2),repeat=4):assert m['run'](values)==tuple(sorted(values,reverse=True))
for hyp,sig in m['signatures']().items():assert m['diagnose'](sig)==hyp
assert m['minimum_fixed_test_count']()==3
results['PREP-030']=dict(healthy_sort_inputs=256,hypotheses=11,strict_order_probes=24,fixed_probe_pairs=276,minimum_nonadaptive_probes=3,signatures={str(k):v for k,v in m['signatures']().items()})

out=BANK/'checks/hardware1115-verification.json'
out.write_text(json.dumps(dict(result='passed',scope='Python logical and finite enumeration models',questions=results),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({key:{k:v for k,v in value.items() if k!='signatures'} for key,value in results.items()},indent=2))
