"""Independent finite oracles. Native simulator evidence is reported separately."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
from random import Random

BANK=Path(__file__).resolve().parents[1]
PATH=BANK/'solutions/prep_reasoning_batch1107n30.py'
spec=importlib.util.spec_from_file_location('n30_reasoning',PATH)
model=importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
counts={}


def check(condition):
    if not condition:
        raise AssertionError('independent oracle failed')


def run():
    cases=0
    for cap in range(3,13):
        for total in range(2,101):
            for seed in range(8):
                sizes=list(model.packetize(total,cap,Random(seed)))
                check(sum(sizes)==total and all(2<=size<=cap for size in sizes))
                cases+=1
    for p in range(1,17):
        totals=sorted({2*p,2*p+1,2*p+2,65535+2*p,65536+2*p,65537+2*p,1000000})
        for total in totals:
            for seed in range(16):
                ports,packets=model.router_plan(total,p,seed)
                check(len(ports)==len(set(ports))==p)
                check({port for port,_ in packets}==set(ports))
                check(all(0<=port<16 and 2<=size<=65536 for port,size in packets))
                check(sum(size for _,size in packets)==total)
                check((ports,packets)==model.router_plan(total,p,seed))
                cases+=1
    for seed in range(128):
        calls=[]
        result=model.random_router_test(1000000,seed,lambda p,n,calls=calls:calls.append((p,n)))
        check(sum(n for _,n in calls)==result['total'])
        check({p for p,_ in calls}==set(result['ports']))
        check(len(calls)==result['packet_count'])
        cases+=1
    counts['router_partition_and_coverage_cases']=cases

    for epoch in range(8):
        phase=0
        for k in range(1024):
            out,next_phase=model.counter_0121(phase)
            check(out==[0,1,2,1][k%4] and next_phase==(k+1)%4)
            phase=next_phase
    counts['counter_samples']=8*1024
    distinguish=0
    for left in range(4):
        for right in range(left+1,4):
            a,b=left,right
            outputs=[]
            for _ in range(4):
                x,a=model.counter_0121(a);y,b=model.counter_0121(b)
                outputs.append(x!=y)
            check(any(outputs));distinguish+=1
    counts['counter_distinguishable_pairs']=distinguish

    cases=0
    for length in range(8):
        for events in itertools.product(range(4),repeat=length):
            occupancy=0
            for event in events:
                expected=occupancy
                reject=event==3 or (event==1 and expected==3) or (event==2 and expected==0)
                if not reject:
                    expected+=(event==1)-(event==2)
                got,lamp,rejected=model.room_step(occupancy,event)
                check((got,lamp,rejected)==(expected,expected>0,reject))
                occupancy=got;cases+=1
    counts['room_trace_steps']=cases
    for i in range(4):
        for j in range(i+1,4):
            a,b=i,j
            for _ in range(i):a=model.room_step(a,2)[0];b=model.room_step(b,2)[0]
            check(a==0 and b>0)
    counts['room_distinguishable_pairs']=6

    cases=0
    for length in range(13):
        for bits in itertools.product((0,1),repeat=length):
            got=model.delayed_left_div3(bits)
            numeric=0;power=1;state=0
            for k,bit in enumerate(bits):
                check(got[k]==(k>0 and numeric%3==0))
                numeric+=bit*power;power*=2
                state=(2*(state+bit))%3
                check(state==(numeric*pow(pow(2,k+1,3),-1,3))%3)
                cases+=1
    counts['div3_prefix_steps_with_numeric_invariant']=cases

    pieces=(1,2,4)
    sums=[sum(v for i,v in enumerate(pieces) if mask&(1<<i)) for mask in range(8)]
    check(sorted(sums)==list(range(8)))
    held=set()
    schedule=model.gold_payments()
    for expected_day,item in enumerate(schedule,1):
        check(item['day']==expected_day)
        for v in item['take_back']:check(v in held);held.remove(v)
        for v in item['give']:check(v not in held);held.add(v)
        check(held==set(item['holds']) and sum(held)==expected_day)
    for cut in range(1,7):
        possible={0,cut,7-cut,7}
        check(possible!=set(range(8)))
    counts['gold_subset_sums']=8
    counts['gold_ownership_transitions']=7
    counts['gold_one_cut_integer_splits']=6

    invalid=[lambda:model.router_plan(1,1),lambda:model.router_plan(31,16),
             lambda:model.router_plan(100,0),lambda:model.router_plan(100,17),
             lambda:model.counter_0121(4),lambda:model.room_step(-1,0),
             lambda:model.room_step(0,4),lambda:model.delayed_left_div3([2])]
    for call in invalid:
        try:call()
        except ValueError:pass
        else:raise AssertionError('invalid input accepted')
    counts['invalid_input_cases']=len(invalid)

    native=BANK/'checks/night1107n30-native-verification.json'
    report={
        'status':'PASS','scope':'Finite independent Python models and exact ownership/state checks',
        'counts':counts,'total_checks':sum(counts.values()),
        'source_sha256':hashlib.sha256(PATH.read_bytes()).hexdigest(),
        'native_evidence_path':str(native.relative_to(BANK)).replace('\\','/'),
        'native_evidence_exists':native.exists(),
        'limitations':['No actual router DUT, network delivery or physical hardware validation.',
                       'Finite enumeration supplements proofs and does not enumerate infinite streams.',
                       'Native SV simulation evidence is separate; no SPICE, STA or hardware signoff.']}
    (BANK/'checks/batch1107n30-reasoning-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':run()
