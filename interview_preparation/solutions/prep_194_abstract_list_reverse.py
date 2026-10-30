"""Completed ADT contract: Empty, is_empty, singleton, Head, Tail and @.

concat copies only its left spine and shares its right suffix. Source did not
define constructors, empty tests or costs: these are explicit extra assumptions.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Node:
    value: object
    next: object = None

def is_empty(chain):
    return chain is None

def singleton(value):
    return Node(value)

def Head(chain):
    if is_empty(chain):
        raise ValueError('Head of empty chain')
    return chain.value

def Tail(chain):
    if is_empty(chain):
        raise ValueError('Tail of empty chain')
    return chain.next

def concat(left, right):
    prefix = []
    while not is_empty(left):
        prefix.append(Head(left)); left = Tail(left)
    for value in reversed(prefix):
        right = Node(value, right)
    return right

def reverse(chain):
    result = None
    while not is_empty(chain):
        result = concat(singleton(Head(chain)), result)
        chain = Tail(chain)
    return result
