"""A current-position list represented by two linked stacks."""


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
        if self.head is None:
            raise IndexError("no element")
        return self.head.value


class CursorList:
    def __init__(self):
        self.left = _Stack()
        self.right = _Stack()

    def get(self):
        return self.right.top()

    def prev(self):
        return self.left.top()

    def next(self):
        current = self.right.pop()
        try:
            return self.right.top()
        finally:
            self.right.push(current)

    def move_prev(self):
        if self.left.empty():
            return False
        self.right.push(self.left.pop())
        return True

    def move_next(self):
        if self.right.empty():
            return False
        current = self.right.pop()
        if self.right.empty():
            self.right.push(current)
            return False
        self.left.push(current)
        return True

    def insert_before(self, value):
        if type(value) is not int:
            raise TypeError("integer value required")
        (self.right if self.right.empty() else self.left).push(value)

    def insert_after(self, value):
        if type(value) is not int:
            raise TypeError("integer value required")
        if self.right.empty():
            self.right.push(value)
        else:
            current = self.right.pop()
            self.right.push(value)
            self.right.push(current)

    def delete(self):
        value = self.right.pop()
        if self.right.empty() and not self.left.empty():
            self.right.push(self.left.pop())
        return value


def cursor_trace(operations):
    """Test adapter; current-relative operations only, no arbitrary node handles."""
    cursor = CursorList()
    output = []
    allowed = {"get", "prev", "next", "move_prev", "move_next",
               "insert_before", "insert_after", "delete"}
    for operation in operations:
        name, *args = operation
        if name not in allowed or len(args) != int(name.startswith("insert_")):
            raise ValueError("invalid operation")
        try:
            output.append({"ok": True, "value": getattr(cursor, name)(*args)})
        except IndexError:
            output.append({"ok": False, "error": "empty_or_boundary"})
    return output
