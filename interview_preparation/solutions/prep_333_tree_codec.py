"""A flat preorder JSON array, with null marking each empty child."""
import json
from dataclasses import dataclass


@dataclass
class Node:
    value: int
    left: object = None
    right: object = None


def serialize(root):
    tokens, pending = [], [root]
    while pending:
        node = pending.pop()
        if node is None:
            tokens.append(None)
        else:
            if type(node.value) is not int:
                raise ValueError("Integer values required")
            tokens.append(node.value)
            pending.extend((node.right, node.left))
    return json.dumps(tokens, separators=(",", ":"))


def deserialize(text):
    tokens = json.loads(text)
    if not isinstance(tokens, list):
        raise ValueError("Token array required")
    root, slots = None, [(None, None)]
    for token in tokens:
        if not slots:
            raise ValueError("Extra token")
        parent, side = slots.pop()
        if token is not None and type(token) is not int:
            raise ValueError("Integer or null required")
        node = None if token is None else Node(token)
        if parent is None:
            root = node
        else:
            setattr(parent, side, node)
        if node is not None:
            slots.extend(((node, "right"), (node, "left")))
    if slots:
        raise ValueError("Incomplete encoding")
    return root


def tree_codec_round_trip(serialized):
    return serialize(deserialize(serialized))
