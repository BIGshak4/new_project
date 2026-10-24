"""64 existing 64-bit payload cells; one logical 32-bit external control word.

Only FREE cells store next indices. Allocated cells may hold ANY uint64 payload
and are never traversed/changed by another allocation. head is in 0..64 (7 bits),
where 64 means empty. Python object overhead is not a four-byte memory claim.
free_index requires a currently allocated index; double/stale free is outside
the contract and is not detected. Invalid index types/ranges are rejected.
"""

NIL = 64


class Pool64:
    __slots__ = ("cells", "head")

    def __init__(self, cells):
        if not isinstance(cells, list) or len(cells) != 64:
            raise ValueError("supply the existing array of exactly 64 payload cells")
        self.cells = cells
        self.head = 0
        for index in range(64):
            cells[index] = index + 1

    def malloc_index(self):
        if self.head == NIL:
            return -1
        index = self.head
        self.head = self.cells[index]
        return index

    def free_index(self, index):
        if type(index) is not int or not 0 <= index < 64:
            raise ValueError("index must be an integer in 0..63")
        # Precondition: caller owns this currently allocated slot.
        self.cells[index] = self.head
        self.head = index
