"""All small private-prefix/shared-suffix lengths, equal values and immutability."""
import sys
from pathlib import Path
from itertools import product
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'solutions'))
from prep_032_list_intersection import Node, intersection

def chain(size, tail=None):
    nodes=[]
    for _ in range(size):
        tail=Node(7,tail)  # Equal values deliberately do not establish sharing.
        nodes.append(tail)
    return tail,nodes

def case(a,b,c):
    shared,ns=chain(c)
    ha,na=chain(a,shared)
    hb,nb=chain(b,shared)
    nodes=na+nb+ns
    before=[(id(n),id(n.next),n.value) for n in nodes]
    assert intersection(ha,hb) is shared
    assert intersection(hb,ha) is shared
    assert before==[(id(n),id(n.next),n.value) for n in nodes]

for a,b,c in product(range(7),repeat=3):
    case(a,b,c)
case(10000,3,7)
case(10000,3,0)
print('PASS: 343 small shapes in both argument orders + 2 long shapes; all equal values, identity match and no list mutation.')
