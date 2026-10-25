"""Prefix-minimum stack; constant pointer/word work per operation.

Every immutable node stores (value, minimum through this node, previous).
Allocation and word comparison are abstract constant-cost primitives. This
is not a Python hard-real-time or fixed-bit-storage guarantee.
"""


class MinStack:
    def __init__(self):
        self._head = None
        self._size = 0

    def __len__(self):
        return self._size

    def push(self, value):
        if type(value) is not int:
            raise ValueError("stack values must be integers")  # noqa: TRY004 - documented invalid-input API
        minimum = value if self._head is None else min(value, self._head[1])
        self._head = (value, minimum, self._head)
        self._size += 1

    def pop(self):
        value = self.top()
        self._head = self._head[2]
        self._size -= 1
        return value

    def top(self):
        if self._head is None:
            raise IndexError("empty stack")
        return self._head[0]

    def find_min(self):
        if self._head is None:
            raise IndexError("empty stack")
        return self._head[1]
