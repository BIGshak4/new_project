"""Test a Python reference, NOT compiled Java or C++."""
from functools import lru_cache
from itertools import product
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'solutions'))
from prep_026_tree_max import Node, maximum

@lru_cache(None)
def shapes(n):
    if n==0:
        return (None,)
    return tuple((left,right) for k in range(n) for left in shapes(k) for right in shapes(n-1-k))

def construct(shape,values):
    if shape is None:
        return None
    value=next(values)
    return Node(value,construct(shape[0],values),construct(shape[1],values))

count=0
for n in range(6):
    for shape in shapes(n):
        for values in product((-1,0,1),repeat=n):
            root=construct(shape,iter(values))
            assert maximum(root)==(max(values) if values else None)
            count+=1
assert maximum(Node(3,Node(99),Node(4)))==99
assert maximum(Node(-5,Node(-20),Node(-8)))==-5
assert maximum(Node(-(2**31)))==-(2**31)
assert maximum(Node(2**31-1))==2**31-1
root=None
for value in range(3000):
    root=Node(value,root,None)
assert maximum(root)==2999
print(f'PASS Python reference: {count} labelled binary trees of size 0..5, non-BST/negative/int-boundary examples and depth-3000 tree. C++/Java compiler unavailable; those sources not compiled or executed.')
