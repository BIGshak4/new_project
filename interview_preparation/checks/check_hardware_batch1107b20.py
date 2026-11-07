"""Independent finite logical checks; native simulator results are separate."""
import importlib.util
import itertools
import json
from pathlib import Path

BANK=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pipe',BANK/'solutions/prep_280_pipeline_model_batch1107b20.py')
pipe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipe)

def main():
    counts={}
    for triple in itertools.product(range(4),repeat=3):
        a,b,c=triple
        if a>b:a,b=b,a
        if b>c:b,c=c,b
        if a>b:a,b=b,a
        assert (a,b,c)==tuple(sorted(triple))
    counts['ordered_sample_triples']=64
    for a,b in itertools.product((0,1),repeat=2):
        x=1-a;y=a if b==0 else x
        assert y==a^b
        assert ((1-a)|b)==int(not(a==1 and b==0))
        nand=lambda x,y:1-(x&y)
        nor=lambda x,y:1-(x|y)
        assert nand(nand(a,b),nand(a,b))==a*b
        assert nor(nor(a,a),nor(b,b))==a*b
        assert nor(nand(a,b),nand(a,b))==a*b
        assert nand(a,nand(b,b))==int(not a or b)
    counts['truth_rows']=4
    # Exhaust all two-NOR DAGs under the stated no-free-inverter model.
    inputs=(0b1100,0b1010);target=0b1000;gate=lambda a,b:(~(a|b))&15
    tested=0
    for i,j in itertools.combinations_with_replacement(range(2),2):
        first=gate(inputs[i],inputs[j]);nodes=inputs+(first,)
        assert first!=target
        for p,q in itertools.combinations_with_replacement(range(3),2):
            assert gate(nodes[p],nodes[q])!=target;tested+=1
    counts['two_nor_networks_excluded']=tested
    transitions=((1,0),(2,0),(2,3),(1,0))
    prefixes=words=0
    for length in range(1,12):
        for bits in itertools.product((0,1),repeat=length):
            state=0;words+=1
            for i,bit in enumerate(bits):
                found=state==3 and bit==0;state=transitions[state][bit]
                assert found==(i>=3 and bits[i-3:i+1]==(0,0,1,0));prefixes+=1
    counts.update(serial_words=words,serial_prefixes=prefixes)
    source='1100100101';expected='0000010010'
    assert ''.join(str(int(source[max(0,i-3):i+1]=='0010'))for i in range(len(source)))==expected
    cases=0
    for k in range(1,9):
        for n in range(1,21):
            trace=pipe.schedule(list(range(n))+[None]*(k-1),stages=k)
            completed=[(cycle,x)for cycle,_,x in trace if x is not None]
            assert completed==[(k+i,i)for i in range(n)]
            assert trace[-1][0]==pipe.ideal_cycles(n,k);cases+=1
    trace=pipe.schedule(['A','B',None,None,'C']+[None]*5,stalls={3,4})
    assert [(c,x)for c,_,x in trace if x is not None]==[(7,'A'),(8,'B'),(9,'C')]
    counts['pipeline_schedules']=cases+1
    result={'status':'passed','scope':'Logical finite models, independent suffix/sort/schedule checks and two-NOR lower-bound enumeration. Not analog transistor characterization.','counts':counts,'source18_example':{'input':source,'output':expected,'matches':[6,9]}}
    Path(__file__).with_name('batch1107b20-hardware-model-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
