"""Alternative for PREP-032: two pointer head switching; node identity, no mutation.

Assumptions: finite acyclic singly linked lists with stable next links. This
function accepts any node class; even overloaded equality is never consulted.
"""


def first_shared_node(head_a, head_b):
    p, q = head_a, head_b
    while p is not q:
        p = head_b if p is None else p.next
        q = head_a if q is None else q.next
    return p
