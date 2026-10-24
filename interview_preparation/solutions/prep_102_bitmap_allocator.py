"""Logical model: one 32-bit occupancy bitmap, no per-slot flag array."""
MASK32 = (1 << 32) - 1


class Pool32:
    __slots__ = ('used',)

    def __init__(self):
        self.used = 0

    def malloc_index(self):
        free = (~self.used) & MASK32
        if free == 0:
            return -1
        bit = free & -free
        self.used |= bit
        return bit.bit_length() - 1

    def free_index(self, index):
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < 32:
            return False
        bit = 1 << index
        if not self.used & bit:
            return False
        self.used &= MASK32 ^ bit
        return True
