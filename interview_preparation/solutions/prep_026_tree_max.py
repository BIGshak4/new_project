"""Python reference model of the iterative Java/C++ algorithms."""
from dataclasses import dataclass


@dataclass
class Node:
    value: int
    left: 'Node | None' = None
    right: 'Node | None' = None


def maximum(root: Node | None) -> int | None:
    if root is None:
        return None
    best = root.value
    pending = [root]
    while pending:
        node = pending.pop()
        best = max(best, node.value)
        if node.right is not None:
            pending.append(node.right)
        if node.left is not None:
            pending.append(node.left)
    return best
