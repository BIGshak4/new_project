"""Reproducible small checks; broad independent oracles are in backend pytest."""
import importlib.util
import itertools
import json
import math
import random
from pathlib import Path

BANK=Path(__file__).resolve().parents[1]


def load(name):
    spec=importlib.util.spec_from_file_location(name,BANK/'solutions'/f'{name}.py')
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(number):
    count=0
    if number==221:
        m=load('prep_221_lpf')
        for r,c in [(1000,1e-9),(10000,1e-8),(330,1e-6)]:
            fc=m.cutoff(r,c)
            assert abs(abs(m.response(r,c,fc))-math.sqrt(0.5))<1e-12
            for ratio in [0,0.1,1,10,100]:
                f=ratio*fc;v=m.response(r,c,f)
                assert abs((1-v)/r-2j*math.pi*f*c*v)<1e-12
                count+=1
    elif number==222:
        m=load('prep_222_integrator')
        for vin,initial,t in itertools.product([-0.2,0,0.1],[0,0.3],[0,0.001,0.004]):
            expected=initial-sum(vin*0.001 for _ in range(round(t/0.001)))/0.001
            assert abs(m.constant_input(10000,100e-9,vin,initial,t)-expected)<1e-12
            count+=1
        assert math.isclose(m.dc_rail_time(10000,100e-9,0.1,0,-5,5),0.05)
    elif number==223:
        m=load('prep_223_ramp_memory');data=bytes(range(256))
        for endian in ['little','big']:
            for start in range(253):
                assert m.expected_word(start,endian)==int.from_bytes(data[start:start+4],endian)
                count+=1
            assert m.validate(lambda a,endian=endian:int.from_bytes(data[a:a+4],endian),endian)==(True,64)
    elif number==227:
        m=load('prep_227_register_copy')
        for width in range(1,7):
            for a,b in itertools.product(range(1 << width),repeat=2):
                assert m.parallel(a,b,width)==(a,a)
                assert m.serial(a,b,width)[:2]==(a,a)
                count+=1
    elif number==15:
        m=load('prep_015_nand_batch22')
        for x,y in itertools.product([0,1],repeat=2):
            assert m.nand(x,y)==int(not (x and y))
            count+=1
        assert m.minimum_direct_cover(False)==m.minimum_direct_cover(True)==3
    elif number==151:
        m=load('prep_151_uint32_popcount_batch22')
        rng=random.Random(15122)
        values=list(range(65536))+[rng.getrandbits(32) for _ in range(1024)]
        values.extend([0,0xffffffff,0x80000000])
        for value in values:
            assert m.popcount(value)==value.bit_count()
            count+=1
    else:
        raise ValueError(number)
    suffix={15:'-nand-drivers-batch22',151:'-uint32-count-batch22'}.get(number,'')
    result={'question_id':f'PREP-{number:03d}','status':'pass','model_cases':count,
            'method':'Executed deterministic Python equation, truth-table, byte or old-state capture checks; independent pytest oracles are separate.',
            'independent_tests':'backend/tests/test_preparation_20261031_batch22_hardware.py',
            'limitations':['No SPICE, HDL compilation, physical measurements or timing signoff.','Proposed C was not compiled in these local Python checks.','Human professional review pending.']}
    path=BANK/'checks'/f'prep-{number:03d}{suffix}-verification.json'
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{result["question_id"]}: {count} Python model cases PASS')
    return result


if __name__=='__main__':
    for item in [221,222,223,227,15,151]:
        check(item)
