"""Public knowledge updates for three hats; tuple order front,middle,rear."""
from itertools import product

WORLDS = [w for w in product('WB',repeat=3) if w.count('B')<=2]

def rear_knows(w):
    candidates=[v for v in WORLDS if v[:2]==w[:2]]
    return len({v[2] for v in candidates})==1

def middle_knows(w):
    candidates=[v for v in WORLDS if v[0]==w[0] and rear_knows(v)==rear_knows(w)]
    return len({v[1] for v in candidates})==1

def front_candidates(w):
    return [v for v in WORLDS if rear_knows(v)==rear_knows(w) and middle_knows(v)==middle_knows(w)]

def check():
    assert len(WORLDS)==7
    transcripts={}
    for w in WORLDS:
        possible_colors={v[0] for v in front_candidates(w)}
        assert possible_colors=={w[0]}
        transcript=(rear_knows(w),middle_knows(w))
        transcripts.setdefault(transcript,set()).add(w[0])
    assert transcripts=={(False,False):{'W'},(False,True):{'B'},(True,True):{'B'}}
    assert sum(rear_knows(w) for w in WORLDS)==1
    print('PASS: all 7 legal color assignments; all 3 possible answer transcripts uniquely determine the front hat.')

if __name__=='__main__':
    check()
