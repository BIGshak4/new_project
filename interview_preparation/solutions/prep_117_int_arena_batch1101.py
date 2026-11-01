"""Logical fixed-int arena model; Python object overhead is not a C claim."""


class IntArena:
    def __init__(self, cells):
        if type(cells) is not int or cells < 0:
            raise ValueError('nonnegative cell count required')
        self.data = list(range(1, cells)) + [-1] if cells else []
        self.head = 0 if cells else -1

    def alloc(self):
        if self.head == -1:
            return None
        index = self.head
        self.head = self.data[index]
        return index

    def release(self, index):
        # Precondition: index is live; no hidden occupancy set in this model.
        self.data[index] = self.head
        self.head = index
