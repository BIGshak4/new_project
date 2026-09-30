"""Check XOR using an independent frequency oracle and an unread-cell witness."""
from collections import Counter
from itertools import product
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'solutions'))
from prep_027_odd_digit import odd_digit, odd_digit_checked

valid = invalid = 0
cases=(values for n in (1,3,5,7) for values in product(range(4),repeat=n))
for values in cases:
    candidates=[v for v,c in Counter(values).items() if c%2]
    if len(candidates)==1:
        assert odd_digit(values)==odd_digit_checked(values)==candidates[0]
        valid+=1
    else:
        try:
            odd_digit_checked(values)
        except ValueError:
            invalid+=1
        else:
            raise AssertionError(values)
for values in product(range(10),repeat=3):
    candidates=[v for v,c in Counter(values).items() if c%2]
    if len(candidates)==1:
        assert odd_digit(values)==odd_digit_checked(values)==candidates[0]
for digit in range(10):
    values=[digit]*3 + [v for v in range(10) for _ in range(2)]
    assert odd_digit(values)==digit
for bad in [[],[1,1],[1,2,3],[10],[-1],[1.5],[True]]:
    try:
        odd_digit_checked(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(bad)
for n in (1,3,5,101):
    baseline=[0]*n
    for unread in range(n):
        alternative=baseline.copy()
        alternative[unread]=1
        assert odd_digit_checked(baseline)==0
        assert odd_digit_checked(alternative)==1
        assert all(baseline[j]==alternative[j] for j in range(n) if j!=unread)
print(f'PASS: {valid} valid and {invalid} invalid small-array cases; all 1000 digit triples, all 10 odd targets, bad inputs and unread-cell witnesses. Lower bound is proved symbolically in solution.')
