"""Check pulse width and fundamental period of five output gate choices."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'solutions'))
from prep_010_divide_by_three import simulate

VARIANTS = {
    'short': (lambda p,d: p & (1-d), lambda duty: duty),
    'p': (lambda p,d: p, lambda duty: 1),
    'or': (lambda p,d: p | d, lambda duty: 1+duty),
    'not_p': (lambda p,d: 1-p, lambda duty: 2),
    'not_short': (lambda p,d: 1-(p & (1-d)), lambda duty: 3-duty),
}

if __name__ == '__main__':
    checked=0
    for duty in (0.1,0.25,0.4,0.5,0.6,0.75,0.9):
        rows=simulate(31,duty=duty)
        for name,(gate,expected_width) in VARIANTS.items():
            values=[gate(r['q1'],r['delayed']) for r in rows]
            rises=[r['t'] for previous,value,r in zip(values,values[1:],rows[1:])
                   if previous==0 and value==1]
            assert all(abs(b-a-3)<1e-9 for a,b in zip(rises,rises[1:])), name
            for cycle in range(10):
                base=cycle*6
                high=sum(values[i]*(rows[i+1]['t']-rows[i]['t'])
                         for i in range(base,base+6))
                assert abs(high-expected_width(duty))<1e-9, (name,duty,high)
                checked+=1
    print(f'PASS: {checked} output periods checked; five gate choices, seven input duty ratios; all periods 3T and pulse widths match formulas. Ideal model only.')
