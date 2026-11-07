"""Classify a finite, closed, stable parent map by identity; never mutate nodes."""


def disconnected_nodes(nodes):
    nodes = list(nodes)
    by_identity = {id(node): node for node in nodes}
    if len(by_identity) != len(nodes):
        raise ValueError('duplicate node identity')
    parents, roots = {}, []
    for node in nodes:
        try:
            parent = node.get_parent()
            marked = node.is_root()
        except AttributeError as error:
            raise TypeError('nodes must provide get_parent() and is_root()') from error
        if type(marked) is not bool:
            raise TypeError('is_root() must return bool')
        if parent is not None and id(parent) not in by_identity:
            raise ValueError('parent is outside the supplied node collection')
        identity = id(node)
        parents[identity] = None if parent is None else id(parent)
        if marked:
            roots.append(identity)
    if len(roots) != 1:
        raise ValueError('exactly one node must be marked as the root')
    # White=unseen, gray=current unresolved path, black=resolved.
    colors = {roots[0]: 2}
    reaches_root = {roots[0]: True}  # Designated root is terminal.
    for node in nodes:
        start = id(node)
        if colors.get(start, 0) == 2:
            continue
        path, cursor = [], start
        while cursor is not None and colors.get(cursor, 0) == 0:
            colors[cursor] = 1
            path.append(cursor)
            cursor = parents[cursor]
        connected = cursor is not None and colors[cursor] == 2 and reaches_root[cursor]
        for identity in reversed(path):
            colors[identity] = 2
            reaches_root[identity] = connected
    return [node for node in nodes if not reaches_root[id(node)]]
