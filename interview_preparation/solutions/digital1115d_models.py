"""Executable models, not analog cell timing or synthesis."""
from collections import deque

def detector1010_step(state, bit):
    if state not in range(4) or bit not in (0,1):raise ValueError("binary state/input")
    return ((0,1),(2,1),(0,3),(2,1))[state][bit], int(state==3 and bit==0)


def stretch_step(previous,remaining,bit,n,reset=False):
    if type(n) is not int or n<1 or remaining not in range(n+1):raise ValueError("positive width and bounded counter")
    if previous not in (0,1) or bit not in (0,1):raise ValueError("binary samples")
    if reset:return 0,0,0
    new=n if bit and not previous else max(0,remaining-1)
    return bit,new,int(new>0)


def thermal_step(on,hot,cold,reset=False):
    if any(v not in (0,1) for v in (on,hot,cold)):raise ValueError("binary state/controls")
    fault=hot & cold
    new=0 if reset or fault or cold else (1 if hot else on)
    return new,fault


def priority_dag():
    """Topological DAG tuples (name,operation,fanins,delay_in_tau)."""
    nodes=[('h6','WIRE',('x7',),0)]
    nodes.extend((f'h{i}','OR',(f'h{i+1}',f'x{i+1}'),0) for i in range(5,-1,-1))
    nodes.extend((f'n{i}','NOT',(f'h{i}',),0) for i in range(7))
    nodes.extend((f'y{i}','AND',(f'x{i}',f'n{i}'),1) for i in range(7))
    nodes.append(('y7','WIRE',('x7',),0))
    return nodes


def evaluate_priority_dag(word, dag=None):
    if type(word) is not int or not 0<=word<=255:raise ValueError("unsigned byte")
    dag=priority_dag() if dag is None else dag
    value={f'x{i}':(word>>i)&1 for i in range(8)}
    arrival={k:0 for k in value}
    for name,op,pins,delay in dag:
        if not 1<=len(pins)<=2:raise ValueError("bounded fan-in")
        args=[value[p] for p in pins]
        value[name]={'WIRE':lambda:args[0],'OR':lambda:args[0]|args[1],
                     'NOT':lambda:1-args[0],'AND':lambda:args[0]&args[1]}[op]()
        arrival[name]=max(arrival[p] for p in pins)+delay
    return sum(value[f'y{i}']<<i for i in range(8)),max(arrival[f'y{i}'] for i in range(8)),arrival


class FifoObserver:
    """Passive reference state, driven by sampled accepted transfers only.

    No bypass; a full FIFO allows a replacement write with an accepted read.
    out_data is sampled pre-edge. Reset is not a traffic transaction.
    """
    def __init__(self,depth):
        if type(depth) is not int or depth<1:raise ValueError("positive depth")
        self.depth=depth;self.expected=deque();self.coverage=set();self.read_values=[]

    def sample(self,in_valid,in_ready,in_data,out_valid,out_ready,out_data,reset=False):
        if reset:
            self.expected.clear();self.coverage.add('reset');return False,False
        count=len(self.expected)
        # Flag contract is independent of requested transfers.
        want_out=(count>0)
        want_in=(count<self.depth) or (want_out and bool(out_ready))
        assert bool(out_valid)==want_out, "out_valid differs from reference occupancy"
        assert bool(in_ready)==want_in, "in_ready differs from specified full replacement rule"
        pop=bool(out_valid and out_ready);push=bool(in_valid and in_ready)
        self.coverage.add(('occupancy',count))
        if out_valid:
            assert out_data==self.expected[0], "FIFO data/order mismatch while valid"
        if pop:
            assert self.expected, "underflow"
            self.read_values.append(self.expected.popleft())
        if push:self.expected.append(in_data)
        if push:self.coverage.add('accepted_write')
        if pop:self.coverage.add('accepted_read')
        if in_valid and not in_ready:self.coverage.add('blocked_write')
        if out_ready and not out_valid:self.coverage.add('blocked_read')
        if push and pop:self.coverage.add('simultaneous')
        assert 0<=len(self.expected)<=self.depth
        return push,pop
