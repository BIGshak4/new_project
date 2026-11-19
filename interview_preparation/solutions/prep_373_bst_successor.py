class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.parent = None


def successor(node):
    """Return the next node in ascending key order, or None."""
    if node is None:
        return None
    if node.right is not None:
        node = node.right
        while node.left is not None:
            node = node.left
        return node

    parent = node.parent
    while parent is not None and node is parent.right:
        node, parent = parent, parent.parent
    return parent


def successors_of_insertion_order(keys):
    """JSON adapter: build the BST, then return successors in input-key order."""
    root = None
    nodes = []
    for key in keys:
        item = Node(key)
        nodes.append(item)
        if root is None:
            root = item
            continue
        cursor = root
        while True:
            branch = 'left' if key < cursor.key else 'right'
            child = getattr(cursor, branch)
            if child is None:
                setattr(cursor, branch, item)
                item.parent = cursor
                break
            cursor = child
    return [found.key if (found := successor(node)) is not None else None
            for node in nodes]
