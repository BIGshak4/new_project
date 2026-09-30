"""Exhaustively check both equation models and all stage invariants."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'solutions'))
from prep_014_isolate_msb import isolate_msb,priority_chain

if __name__ == '__main__':
    for x in range(256):
        expected=0 if x==0 else 1 << (x.bit_length()-1)
        y=isolate_msb(x)
        assert y==priority_chain(x)==expected
        assert y & x == y
        assert y==0 or y & (y-1)==0
        s=x
        width=1
        for shift in (1,2,4):
            s |= s >> shift
            width *= 2
            for bit in range(8):
                window=(x >> bit)&((1<<min(width,8-bit))-1)
                assert ((s>>bit)&1)==int(window!=0)
        assert s==(0 if x==0 else (1<<x.bit_length())-1)
        assert y==(s & ~(s>>1))
    assert isolate_msb(0b00101011)==0b00100000
    for bad in (-1,256):
        try:
            isolate_msb(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid width accepted')
    print('PASS: all 256 inputs, source example, ripple equivalence, one-hot/zero output and every OR-stage invariant. Python Boolean model, not HDL simulation.')
