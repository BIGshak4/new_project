"""Exhaustive color arrays plus object preservation and classification counts."""
from collections import Counter
from itertools import product
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'solutions'))
from prep_019_three_colors import sort_three_colors

rank={'B':0,'G':1,'R':2}
def check(colors):
    # Identity accompanies color, so replacing balls by freshly generated colors fails.
    items=[(color,i) for i,color in enumerate(colors)]
    original=items.copy();seen=Counter();same=id(items)
    def classify(item):
        seen[item[1]]+=1
        return item[0]
    out=sort_three_colors(items,classify)
    assert id(out)==same
    assert Counter(out)==Counter(original)
    assert [rank[c] for c,_ in out]==sorted(rank[c] for c in colors)
    assert all(seen[i]==1 for i in range(len(colors)))
    assert sum(seen.values())==len(colors)

count=0
for n in range(9):
    for colors in product('BGR',repeat=n):
        check(colors);count+=1
check('BRRBGBRGBGRGGRBB')
for n in (1,10,1000):
    for c in 'BGR':check(c*n)
check('R'*500+'G'*500+'B'*500)
check('B'*500+'G'*500+'R'*500)
print(f'PASS: {count} exhaustive arrays of length 0..8, screenshot sequence, monochrome and length-1500 edge cases.')
print('Same list, same objects, B/G/R order; each original object classified exactly once (array positions may be revisited).')
