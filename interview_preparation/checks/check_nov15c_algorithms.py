"""Independent pair, rank/count and exact-unit Fermi verification."""
import hashlib
import itertools
import json
import runpy
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
pair_path=ROOT/'solutions/prep_211_maximum_pair_sum_1115c.py'
pair=runpy.run_path(str(pair_path))['maximum_pair_sum']
old=runpy.run_path(str(ROOT/'solutions/prep_211_top_two_and_mode.py'))

def pair_oracle(values):
    candidates=[values[i]+values[j] for i in range(len(values)) for j in range(i+1,len(values))]
    return max(candidates) if candidates else None

class SingleTraversal:
    def __init__(self,values):self.values=values;self.calls=0
    def __iter__(self):
        self.calls+=1
        if self.calls!=1:raise AssertionError('second traversal')
        yield from self.values

def main():
    checked=0
    for length in range(8):
        for items in itertools.product(range(5),repeat=length):
            values=list(items);before=values[:]
            assert pair(values)==pair_oracle(values)
            assert values==before
            checked+=1
    boundary=[[],[0],[0,0],[5,5],[7,1,7],[4,9,2,9],
              [2**1000,2**1000+7,0,2**999],[2**32-1,2**32-1]]
    for values in boundary:
        stream=SingleTraversal(values)
        assert pair(stream)==pair_oracle(values) and stream.calls==1
    for values in ([True],[False],[1,-1],[1,1.0],['1'],[None]):
        try:pair(values)
        except ValueError:pass
        else:raise AssertionError('invalid natural accepted')
    previous=0
    for length in range(8):
        for values in itertools.product((-2,0,3),repeat=length):
            counter=Counter(values);largest=sorted(counter,reverse=True)
            slots=[(x,counter[x]) for x in largest[:2]]+[None,None]
            assert old['top_two_distinct'](values)==tuple(slots[:2])
            mode=min(counter,key=lambda x:(-counter[x],x)) if counter else None
            assert old['mode_with_count'](values)==((mode,counter[mode]) if counter else None)
            previous+=1
    demand=4_000_000*40*Fraction(1,10)
    capacity=4*6*12*35
    stations=demand/capacity
    assert demand==16_000_000 and capacity==10_080
    assert stations==Fraction(100_000,63)
    fills=demand/35
    assert fills/(4*6*12)==stations
    alternate=Fraction(4_000_000,8)/(4*6*12)
    assert alternate==Fraction(15_625,9)
    assert 1500<stations<1600 and 1700<alternate<1800
    ratios=[Fraction(d,c) for d,c in itertools.product((12_000_000,20_000_000),(8_000,16_000))]
    assert min(ratios)==750 and max(ratios)==2500
    for factor in (Fraction(1,2),Fraction(2),Fraction(3)):
        assert demand*factor/capacity==stations*factor
        assert demand/(capacity*factor)==stations/factor
    evidence={
      'result':'passed','pair_arrays':checked,'single_traversal_boundaries':len(boundary),
      'invalid_inputs':6,'preserved_distinct_rank_mode_arrays':previous,
      'fermi':{'demand_litres_day':int(demand),'capacity_litres_station_day':capacity,
               'stations_exact':str(stations),'alternative_exact':str(alternate),
               'scenario_min':750,'scenario_max':2500,'scenario_corners':len(ratios),
               'status':'Illustrative assumed values; no real-world census verified'},
      'sha256':{str(pair_path.relative_to(ROOT)):hashlib.sha256(pair_path.read_bytes()).hexdigest()}
    }
    (ROOT/'checks/nov15c-algorithms-verification.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf8')
    for number in (211,358):
        (ROOT/f'checks/prep-{number}-1115c-verification.json').write_text(json.dumps({'question_id':f'PREP-{number}','result':'passed','evidence':'checks/nov15c-algorithms-verification.json'},indent=2)+'\n',encoding='utf8')
    print(json.dumps(evidence))

if __name__=='__main__':main()
