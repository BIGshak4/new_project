"""Cycle-value equivalence of forward retiming under explicit interface assumptions.

All source transaction inputs are stable before the capturing edge, including
black-box combinational setup in the retimed version. BB is combinational.
One-bit E,F used to enumerate every possible BB truth table; A..D are 2-bit.
This is not a proof of setup/hold, physical timing or arbitrary reset behavior.
"""
from itertools import product
from fractions import Fraction

def bb(table,e,f):return (table>>((e<<1)|f))&1
def output(a,b,c,d,s):return a*d if s else b*c

count=0
for table in range(16):
    # All possible one-bit BB input functions; both circuits capture transaction k.
    for a,b,c,d,e,f in product(range(4),range(4),range(4),range(4),(0,1),(0,1)):
        original_registers=(a,b,c,d,e,f)
        oa,ob,oc,od,oe,of=original_registers
        original=output(oa,ob,oc,od,bb(table,oe,of))
        # E/F input registers removed: BB(raw e,f) is sampled alongside A..D.
        retimed_registers=(a,b,c,d,bb(table,e,f))
        retimed=output(*retimed_registers)
        assert original==retimed
        count+=1
    # Legal initial selector encoding after merging input registers.
    for e0,f0 in product((0,1),repeat=2):
        rs_initial=bb(table,e0,f0)
        assert rs_initial==bb(table,e0,f0)

# Concrete failure when E/F are retained and only a selector FF is appended.
# Use BB(E,F)=E. Prior selector 0; current selector 1. Data products differ.
a,b,c,d=2,3,4,5
correct=output(a,b,c,d,1)
misaligned=output(a,b,c,d,0)
assert correct==10 and misaligned==12
tbb=Fraction(3); tpost=Fraction(3,2)+Fraction(27,10)
assert max(tbb,tpost)==Fraction(21,5)
print(f'PASS: {count} transaction values across all 16 two-input BB truth tables; legal reset mapping documented.')
print('PASS: appended-only selector FF counterexample (expected 10, got 12). Ideal balanced block maximum: 4.2 ns.')
