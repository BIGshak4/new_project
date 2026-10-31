"""Destructively merge disjoint, acyclic sorted integer lists.

Node identity is preserved. Equal values prefer the lower input-list index;
within each input list order is preserved. The caller relinquishes the old
independent-list topology. Sortedness, disjointness and acyclicity are promises.
"""
import heapq


class Node:
    def __init__(self, value, next_node=None):
        self.value = value
        self.next = next_node


def merge_k_lists(heads):
    heap = [(node.value, index, node) for index, node in enumerate(heads) if node is not None]
    heapq.heapify(heap)
    sentinel = Node(None)
    tail = sentinel
    while heap:
        _, index, node = heapq.heappop(heap)
        successor = node.next
        tail.next = node
        tail = node
        if successor is not None:
            heapq.heappush(heap, (successor.value, index, successor))
    tail.next = None
    return sentinel.next


def merge_sorted_lists(values):
    """Execution adapter: build list nodes from nested arrays, return values."""
    heads = []
    for sequence in values:
        head = None
        for value in reversed(sequence):
            head = Node(value, head)
        heads.append(head)
    out, node = [], merge_k_lists(heads)
    while node is not None:
        out.append(node.value)
        node = node.next
    return out
