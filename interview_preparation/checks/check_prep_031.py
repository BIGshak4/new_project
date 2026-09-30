"""Exhaustive truth tables and all ordinary one-MUX raw-input wirings."""
from itertools import product

def mux(s, i0, i1):
    return i1 if s else i0

def xor_with_zero(a,b):
    t = mux(b,a,0)
    return mux(a,b,t)

def check():
    for a,b in product((0,1),repeat=2):
        assert xor_with_zero(a,b) == a ^ b
        assert (0,b,a,0)[2*a+b] == a ^ b  # optional 4:1 alternative
    raw = [(0,0,0,0),(0,0,1,1),(0,1,0,1)] # 0,a,b
    target = (0,1,1,0)
    for s,i0,i1 in product(raw,repeat=3):
        assert tuple(mux(*v) for v in zip(s,i0,i1)) != target
    assert target not in raw  # zero-MUX alternatives
    print('PASS: four truth-table rows, all 27 one-MUX wirings excluded, and 4:1 variant verified.')

if __name__ == '__main__':
    check()
