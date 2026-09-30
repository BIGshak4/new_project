"""First shared node in finite acyclic singly linked lists; compare identity."""
from dataclasses import dataclass

@dataclass(eq=False)
class Node:
    value: object
    next: 'Node | None' = None

def length(head):
    count = 0
    while head is not None:
        count += 1
        head = head.next
    return count

def intersection(head_a, head_b):
    if head_a is None or head_b is None:
        return None
    n, m = length(head_a), length(head_b)
    p, q = head_a, head_b
    for _ in range(max(n - m, 0)):
        p = p.next
    for _ in range(max(m - n, 0)):
        q = q.next
    while p is not q:
        p = p.next
        q = q.next
    return p
