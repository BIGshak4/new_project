"""Conditional source interpretation: bubble on right select is inversion."""
from fractions import Fraction as F
from itertools import product

def mux(s,d0,d1):return d1 if s else d0
def original(a,b,c,d,s):return mux(s,c,d)*mux(1-s,a,b)
def swapped(a,b,c,d,s):return mux(s,c,d)*mux(s,b,a)
def duplicated(a,b,c,d,s):return mux(s,b*c,a*d)

count=0
for a,b,c,d in product(range(8),repeat=4):
    for s in (0,1):
        assert original(a,b,c,d,s)==swapped(a,b,c,d,s)==duplicated(a,b,c,d,s)
        count+=1
bb,inv,mx,mult=F(3),F(1,10),F(3,2),F(27,10)
left=max(F(0),bb)+mx
right=max(F(0),bb+inv)+mx
before=max(left,right)+mult
after=max(F(0),bb)+mx+mult
speculative=max(bb,mult)+mx
assert (before,after,speculative)==(F(73,10),F(72,10),F(9,2))
assert mx+mult==F(42,10)
print(f'PASS: {count} operand/select combinations; original, swapped-input and duplicated-multiplier functions equivalent.')
print('Timing (ideal given-delay model): original 7.3 ns; input-swap simplification 7.2 ns; TWO-multiplier alternative 4.5 ns.')
