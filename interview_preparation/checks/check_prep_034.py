"""Functionality and structural model checks, not timing/area synthesis."""
import random
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'solutions'))
from prep_034_recursive_carry_select import full_adder,carry_select,cost,delay,best_levels

truth=[]
for a in (0,1):
    for b in (0,1):
        for c in (0,1):
            s,co=full_adder(a,b,c)
            assert s+2*co==a+b+c
            truth.append((a,b,c,s,co))
cases=0
for width in (1,2,4):
    for levels in range(width.bit_length()):
        for a in range(1<<width):
            for b in range(1<<width):
                for c in (0,1):
                    s,co=carry_select(a,b,width,levels,c)
                    assert s+(co<<width)==a+b+c
                    cases+=1
rng=random.Random(34)
values=[(0,0,0),(0,0,1),(0xffffffff,1,0),(0xffffffff,0xffffffff,1),(0x7fffffff,1,0),(0xaaaaaaaa,0x55555555,1)]
values += [(rng.getrandbits(32),rng.getrandbits(32),rng.randrange(2)) for _ in range(1000)]
for a,b,c in values:
    for n in range(6):
        s,co=carry_select(a,b,32,n,c)
        assert s+(co<<32)==a+b+c
expected=[(32,0),(48,17),(72,44),(108,89),(162,170),(243,332)]
assert [cost(32,n) for n in range(6)]==expected
for n in range(6):
    f=32*3**n//2**n
    m=32*(3**n-2**n)//2**n+(3**n-1)//2
    assert cost(32,n)==(f,m)
assert [delay(32,n,1,1) for n in range(6)]==[32,17,10,7,6,6]
assert best_levels(32,1,1)==4
assert best_levels(32,1,0.5)==5
assert best_levels(32,1,20)==0
print(f'PASS: 8 FA rows, {cases} exhaustive small-width cases, {len(values)*6} 32-bit/level cases, cost formulas and delay-model optima. No synthesis or physical timing claim.')
