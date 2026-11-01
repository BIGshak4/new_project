"""Destructive reversal of a caller-owned, finite acyclic singly linked list."""


class Node:
    def __init__(self, value, next_node=None):
        self.value, self.next = value, next_node


def reverse_list(head):
    previous, current = None, head
    while current is not None:
        successor = current.next
        current.next = previous
        previous, current = current, successor
    return previous


def reverse_values(values):
    """Array adapter checks values only; node identity is tested separately."""
    head = None
    for value in reversed(values):
        head = Node(value, head)
    node, result = reverse_list(head), []
    while node is not None:
        result.append(node.value)
        node = node.next
    return result
