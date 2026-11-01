"""Independent finite oracles for the November hardware source intake."""
import importlib.util
import itertools
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOL=ROOT/'interview_preparation/solutions'


def load(name):
    spec=importlib.util.spec_from_file_location(name,SOL/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def report(number,cases,scope):
    return {'question_id':f'PREP-{number:03d}','passed':True,'python_executed':True,
            'cases':cases,'scope':scope,'professional_review':'pending',
            'native_rtl_evidence':'checks/batch1101-hardware-native-verification.json' if number!=233 else None}


def check233():
    module=load('prep_233_ir_drop');cases=0
    for source,current,rs,rg in itertools.product([0,1,3.3],[0,.5,2,5],[0,.015,.05],[0,.005,.02]):
        r=module.dc_rail(source,current,rs,rg)
        ground=current*rg;supply=source-current*rs
        assert math.isclose(r['load_voltage'],supply-ground,abs_tol=1e-12)
        assert math.isclose(source*current,r['load_voltage']*current+r['loss_watts'],abs_tol=1e-12)
        assert math.isclose(r['drop'],source-r['load_voltage'],abs_tol=1e-12)
        cases+=1
    assert math.isclose(module.allowed_resistance(.03,2),.015)
    assert math.isclose(module.ideal_reservoir_capacitance(1,1e-6,.02),50e-6)
    return report(233,cases+2,'KVL via separate supply/ground potentials, power conservation, resistance and ideal charge-budget examples. No SPICE/physical signoff.')


def check234():
    module=load('prep_234_controlled_predicates')
    for value,mode in itertools.product(range(16),range(4)):
        ones=value.bit_count()
        expected=[ones<4,ones>2,ones%2==1,ones%2==0][mode]
        assert module.controlled(value,mode)==expected
    return report(234,64,'Every data/control combination versus independent population counting; zero, strict-majority tie and parity boundaries.')


def check235():
    module=load('prep_235_late_mux')
    for data,select in itertools.product(itertools.product([0,1],repeat=8),range(8)):
        assert module.evaluate(data,select)==(data[select],data[select])
    assert module.worst_data_arrival([8,0,0,0,0,0,0,0],1)==11
    assert module.worst_data_arrival([8,0,0,0,0,0,0,0],1,True)==9
    assert module.worst_data_arrival([0]*8,1,True)==4
    return report(235,2051,'All 2048 binary data/select combinations against direct indexing; arrival example and counterexample when data is simultaneous.')


def check236():
    module=load('prep_236_decoder_mux');cases=0
    for n in [1,2,3]:
        width=2**n
        for data,select in itertools.product(itertools.product([0,1],repeat=width),range(width)):
            actual,decoded=module.decoder_mux(data,select)
            assert actual==data[select]
            assert sum(decoded)==1 and decoded.index(1)==select
            cases+=1
    return report(236,cases,'All data/select pairs for n1..3 against direct indexing; exact decoded one-hot index. Native SV separately exhausts n4.')


def edge_oracle(events):
    out=[]
    for end in range(1,len(events)+1):
        prefix=events[:end]
        data=[value for kind,value in prefix if kind=='data']
        current=data[-1] if data else 0
        clocks=[i for i,(kind,_) in enumerate(prefix) if kind=='clock']
        earlier=prefix[:clocks[-1]] if clocks else []
        sampled=[value for kind,value in earlier if kind=='data']
        previous=sampled[-1] if sampled else 0
        out.append([int(current>previous),int(current<previous),int(current!=previous)])
    return out


def check091():
    module=load('prep_091_polarity_batch1101');cases=0
    for length in range(9):
        for events in itertools.product([('data',0),('data',1),('clock',None)],repeat=length):
            assert module.edge_events(events)==edge_oracle(events)
            cases+=1
    return report(91,cases,'Every data0/data1/clock history through length8 against prefix-history last-sample oracle; repeated changes before a clock included.')


CHECKS={233:check233,234:check234,235:check235,236:check236,91:check091}


if __name__=='__main__':
    for number,check in CHECKS.items():
        result=check()
        name=f'prep-{number:03d}-verification.json' if number!=91 else 'prep-091-polarity-batch1101-verification.json'
        (Path(__file__).parent/name).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(f'PREP-{number:03d}: {result["cases"]} pass')
