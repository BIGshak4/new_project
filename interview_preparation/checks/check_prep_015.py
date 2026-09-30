"""Static tri-state verification and exact cell search for acyclic binary nets.

Each component input must be a fully driven Boolean net in every input case.
Joined outputs may contain Z drivers but must resolve without contention.
No feedback, external pull devices, or free complemented inputs are allowed.
"""
from heapq import heappop, heappush
from itertools import combinations_with_replacement, product

def A(a,b):
    assert a in (0,1) and b in (0,1)
    return 1 if (a,b)==(0,0) else 'Z'

def B(a,b):
    assert a in (0,1) and b in (0,1)
    return 0 if (a,b)==(1,1) else 'Z'

def resolve(*drivers):
    active={v for v in drivers if v!='Z'}
    assert len(active)==1, f'Floating or conflicting net: {drivers}'
    return active.pop()

def xor_circuit(x,y):
    n=resolve(A(x,y),B(x,x),B(y,y))
    out=resolve(A(x,n),A(y,n),B(x,y),B(n,n))
    return n,out

def xor_eight_cells(x,y):
    nx=resolve(A(x,x),B(x,x))
    ny=resolve(A(y,y),B(y,y))
    drivers=(A(x,ny),A(nx,y),B(x,y),B(nx,ny))
    out=resolve(*drivers)
    assert sum(v!='Z' for v in drivers)==1
    return nx,ny,drivers,out

def covers(masks):
    # Minimum number of permitted same-polarity drivers to cover each mask.
    best=[99]*16; best[0]=0
    for mask in range(16):
        for m in masks:
            union=mask|m
            best[union]=min(best[union],best[mask]+1)
    return best

def minimum_cells(free_constants=False):
    # Truth table mask bit k is value on (x,y)=binary(k); x=1100, y=1010.
    initial=(1<<12)|(1<<10)
    if free_constants: initial|=(1<<0)|(1<<15)
    dist={initial:0}; queue=[(0,initial)]
    parent={}; settled=0
    while queue:
        cost,state=heappop(queue)
        if cost!=dist[state]: continue
        settled+=1
        if state&(1<<6):
            path=[]; current=state
            while current!=initial:
                prev,f,w=parent[current]; path.append((f,w)); current=prev
            return cost,list(reversed(path)),settled
        funcs=[f for f in range(16) if state&(1<<f)]
        pairs=list(combinations_with_replacement(funcs,2))
        up=covers({15^(a|b) for a,b in pairs})
        down=covers({a&b for a,b in pairs})
        for f in range(16):
            if state&(1<<f): continue
            w=up[f]+down[15^f]
            if w>=99 or cost+w>7: continue
            nxt=state|(1<<f); c=cost+w
            if c<dist.get(nxt,99):
                dist[nxt]=c; parent[nxt]=(state,f,w); heappush(queue,(c,nxt))
    raise AssertionError('No construction found within seven cells')

if __name__=='__main__':
    for x,y in product((0,1),repeat=2):
        nx,ny,drivers,out=xor_eight_cells(x,y)
        assert nx==1-x and ny==1-y and out==x^y
        print(f'8-cell alternative: x={x}, y={y}, nx={nx}, ny={ny}, drivers={drivers}, out={out}; PASS')
    for x,y in product((0,1),repeat=2):
        n,out=xor_circuit(x,y)
        assert n==int(not(x or y)) and out==(x^y)
        print(f'x={x}, y={y}, n={n}, XOR={out}; both nets fully driven, no contention')
    for constants in (False,True):
        result,path,states=minimum_cells(constants)
        print(f'free_constants={constants}: minimum={result}; path={path}; settled={states}')
        assert result==7
    print('PASS: static behavior and minimum seven cells in the stated acyclic Boolean-net model.')
