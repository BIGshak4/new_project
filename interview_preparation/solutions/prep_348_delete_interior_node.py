"""Logical value deletion with an owned successor and constant-size payload."""


class Node:
    def __init__(self, value, following=None):
        self.value = value
        self.next = following


def delete_given(node):
    if node is None or node.next is None:
        raise ValueError("a valid non-tail node is required")
    successor = node.next
    node.value = successor.value
    node.next = successor.next


def delete_interior_result(values, index):
    """JSON test adapter. The supplied node is strictly inside an acyclic list."""
    if type(index) is not int or not 0 < index < len(values) - 1:
        raise ValueError("index must be strictly between head and tail")
    head = None
    for value in reversed(values):
        head = Node(value, head)
    target = head
    for _ in range(index):
        target = target.next
    delete_given(target)
    result = []
    current = head
    while current is not None:
        result.append(current.value)
        current = current.next
    return result
