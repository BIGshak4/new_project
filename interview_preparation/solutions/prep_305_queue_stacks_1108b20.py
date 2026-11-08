"""Two stacks, enqueue O(1), dequeue/peek amortized O(1)."""


class _Node:
    __slots__ = ("next", "value")

    def __init__(self, value, next_node):
        self.value = value
        self.next = next_node


class _Stack:
    def __init__(self):
        self.head = None

    def empty(self):
        return self.head is None

    def push(self, value):
        self.head = _Node(value, self.head)

    def pop(self):
        value = self.top()
        self.head = self.head.next
        return value

    def top(self):
        if self.empty():
            raise IndexError("empty queue")
        return self.head.value


class TwoStackQueue:
    def __init__(self):
        self.incoming = _Stack()
        self.outgoing = _Stack()

    def enqueue(self, value):
        if type(value) is not int:
            raise TypeError("integer value required")
        self.incoming.push(value)

    def _prepare(self):
        if self.outgoing.empty():
            while not self.incoming.empty():
                self.outgoing.push(self.incoming.pop())

    def dequeue(self):
        self._prepare()
        return self.outgoing.pop()

    def peek(self):
        self._prepare()
        return self.outgoing.top()

    def is_empty(self):
        return self.incoming.empty() and self.outgoing.empty()


def queue_trace(operations):
    """Pure transcript adapter; errors do not change the abstract queue."""
    queue = TwoStackQueue()
    output = []
    allowed = {"enqueue", "dequeue", "peek", "is_empty"}
    for operation in operations:
        name, *args = operation
        if name not in allowed or len(args) != int(name == "enqueue"):
            raise ValueError("invalid operation")
        try:
            output.append({"ok": True, "value": getattr(queue, name)(*args)})
        except IndexError:
            output.append({"ok": False, "error": "empty"})
    return output
