class MaxStack:
    def __init__(self):
        self.head = None

    def push(self, value):
        if type(value) is not int:
            raise ValueError("stack values must be integers")
        previous = self.head
        maximum = value if previous is None else max(value, previous[1])
        self.head = (value, maximum, previous)

    def top(self):
        if self.head is None:
            raise IndexError("empty stack")
        return self.head[0]

    def max(self):
        if self.head is None:
            raise IndexError("empty stack")
        return self.head[1]

    def pop(self):
        value = self.top()
        self.head = self.head[2]
        return value
