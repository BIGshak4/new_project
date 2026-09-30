"""Compare closed form with direct elimination and test boundary identities."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'solutions'))
from prep_012_josephus import survivor, survivor_with_loop, simulate


if __name__ == '__main__':
    assert simulate(5) == ([2,4,1,5], 3)
    for n in range(1, 2049):
        removed, actual = simulate(n)
        assert survivor(n) == survivor_with_loop(n) == actual
        assert len(removed) == n-1
        assert set(removed) | {actual} == set(range(1,n+1))
    for k in (1,2,5,10,31,63,127,1024):
        p = 1 << k
        assert survivor(p) == 1
        assert survivor(p-1) == p-1
        assert survivor(p+1) == 3
    for fun in (survivor,survivor_with_loop,simulate):
        for n in (0,-1,-43):
            try:
                fun(n)
            except ValueError:
                pass
            else:
                raise AssertionError('Expected invalid-size rejection')
    removed, answer = simulate(43)
    assert answer == 23 and removed[:11] == list(range(2,23,2))
    print('PASS: source five-person order; n=1..2048 against simulation; large power-of-two boundaries through 1024-bit exponent; invalid nonpositive inputs; n=43 gives 23.')
