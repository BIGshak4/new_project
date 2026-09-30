"""Build actual gate netlists, count cells and exhaustively compare outputs.

OR/AND/XOR have fan-in two; NOT has fan-in one. Each counted cell costs one
unit in its corresponding abstract library. No area optimality is inferred.
"""
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'solutions'))
from prep_014_isolate_msb import isolate_msb,shared_prefix_xor


def build(kind):
    gates=[]
    def gate(op,*inputs):
        name=f'g{len(gates)}'
        gates.append((name,op,inputs))
        return name
    y={7:'x7'}
    if kind=='independent':
        for i in range(6,-1,-1):
            higher='x7'
            for j in range(6,i,-1):
                higher=gate('OR',higher,f'x{j}')
            y[i]=gate('AND',f'x{i}',gate('NOT',higher))
    elif kind=='shared_basic':
        higher='x7'
        for i in range(6,-1,-1):
            y[i]=gate('AND',f'x{i}',gate('NOT',higher))
            if i>0:
                higher=gate('OR',higher,f'x{i}')
    elif kind=='shared_xor':
        p={7:'x7'}
        for i in range(6,-1,-1):
            p[i]=gate('OR',f'x{i}',p[i+1])
            y[i]=gate('XOR',p[i],p[i+1])
    else:
        raise ValueError(kind)
    return gates,y


def evaluate(gates,outputs,x):
    values={f'x{i}':(x>>i)&1 for i in range(8)}
    for name,op,inputs in gates:
        args=[values[s] for s in inputs]
        if op=='NOT': v=1-args[0]
        elif op=='OR': v=args[0]|args[1]
        elif op=='AND': v=args[0]&args[1]
        elif op=='XOR': v=args[0]^args[1]
        else: raise AssertionError(op)
        values[name]=v
    return sum(values[outputs[i]]<<i for i in range(8))


if __name__=='__main__':
    expected={
        'independent':Counter(OR=21,AND=7,NOT=7),
        'shared_basic':Counter(OR=6,AND=7,NOT=7),
        'shared_xor':Counter(OR=7,XOR=7),
    }
    for kind,counts in expected.items():
        gates,outputs=build(kind)
        assert Counter(op for _,op,_ in gates)==counts
        for x in range(256):
            assert evaluate(gates,outputs,x)==isolate_msb(x)==shared_prefix_xor(x)
        print(f'{kind}: {len(gates)} gates; {dict(counts)}; all 256 inputs PASS')
    print('Counts assume two-input cells, NOT cells and free wires. XOR unit count does not imply equal silicon area. No global minimum claimed.')
