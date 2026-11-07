"""Independent finite reference checks; native HDL proof is recorded separately."""
import itertools
import json
import random
from collections import deque
from pathlib import Path


def validate_sudoku(board):
    if len(board)!=9 or any(len(row)!=9 for row in board):return False
    target=set(range(1,10))
    groups=[list(row) for row in board]
    groups += [[board[r][c] for r in range(9)] for c in range(9)]
    groups += [[board[r+i][c+j] for i in range(3) for j in range(3)] for r in (0,3,6) for c in (0,3,6)]
    return all(set(g)==target and len(g)==9 for g in groups)

def validate_solver_output(output):
    lines=output.splitlines();boards=[]
    for i,line in enumerate(lines):
        if line.startswith('BOARD '):
            board=[list(map(int,lines[i+1+r].split())) for r in range(9)]
            assert validate_sudoku(board),board
            boards.append(board)
    assert len(boards)==2, len(boards)
    return boards

def main():
    counts={}
    for window in (1,2,3,1000):
        hist=deque([0]*window,maxlen=window);left=0
        data=([1]+[0]*1001+[1,1]+[0]*1001) if window==1000 else [int(x) for x in '0010011100001010']
        for b in data:
            hist.append(b);left=window if b else max(0,left-1)
            assert bool(left)==bool(any(hist))
        counts['window_samples']=counts.get('window_samples',0)+len(data)
    for a,b in itertools.product(range(4),repeat=2):
        mux=lambda s,d0,d1:d1 if s else d0
        a1,a0=divmod(a,2);b1,b0=divmod(b,2);t=a0|b0
        y=2*(a1|b1)+mux(a1,mux(b1,t,b0),mux(b1,a0,t))
        assert y==max(a,b)
    counts['max_pairs']=16
    words=prefixes=0
    for length in range(1,12):
        for bits in itertools.product((0,1),repeat=length):
            words+=1;ms=ls=n=lo=0;suffix=0
            for pos,b in enumerate(bits):
                ms=(2*ms+b)%5;ls=(3*(ls+b))%5;suffix=(2*suffix+b)%4
                n=2*n+b;lo+=b*(1<<pos);prefixes+=1
                assert (ms==0)==(n%5==0)
                assert (ls==0)==(lo%5==0)
                assert (suffix==0)==(n%4==0)
    counts.update(serial_words=words,serial_prefixes=prefixes)
    # Boolean edge semantics are checked against a separate deque model.
    queue=deque();rng=random.Random(110710);fifo_checks=0
    mem=[None]*4;rp=wp=n=0
    for _ in range(10000):
        iv,ready=rng.randrange(2),rng.randrange(2);d=rng.randrange(256)
        pop=bool(n and ready);accept=(n<4 or pop);push=bool(iv and accept)
        assert bool(n)==bool(queue)
        if n:assert mem[rp]==queue[0]
        if pop:assert mem[rp]==queue.popleft();rp=(rp+1)%4
        if push:mem[wp]=d;wp=(wp+1)%4;queue.append(d)
        n+=int(push)-int(pop);assert n==len(queue) and 0<=n<=4
        fifo_checks+=1
    counts['fifo_cycles']=fifo_checks
    # Checker acceptance and rejection, not native constraint generation.
    board=[[(r*3+r//3+c)%9+1 for c in range(9)] for r in range(9)]
    assert validate_sudoku(board)
    for r,c in itertools.product(range(9),repeat=2):
        bad=[row[:] for row in board];bad[r][c]=bad[r][(c+1)%9]
        assert not validate_sudoku(bad)
    counts['sudoku_checker_cases']=82
    result={'status':'passed','scope':'Independent Python finite models; not HDL compilation or native SV constraint solving.','counts':counts}
    Path(__file__).with_name('batch1107b10-hardware-model-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
