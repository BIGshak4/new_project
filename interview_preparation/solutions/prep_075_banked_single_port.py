"""One logical word per physical single-port macro; synchronous read model.

The model uses each macro's address zero only. `None` denotes unwritten data,
not a guaranteed physical zero. A control reset clears validity, not memory.
"""
from __future__ import annotations


class SinglePortMacro:
    def __init__(self, depth: int):
        self.mem: list[int | None] = [None] * depth
        self.read_data: int | None = None

    def edge(self, read: bool, write: bool, data: int) -> None:
        if read and write:
            raise AssertionError("primitive cannot read and write together")
        if write:
            self.mem[0] = data
        elif read:
            self.read_data = self.mem[0]


class BankedOneReadOneWrite:
    def __init__(self, depth: int, width: int):
        if depth < 1 or width < 1:
            raise ValueError("depth and width must be positive")
        self.depth, self.width = depth, width
        self.banks = [SinglePortMacro(depth) for _ in range(depth)]
        self.read_addr_q = 0
        self.collision_q = False
        self.write_data_q = 0
        self.rd_valid = False

    @property
    def read_data(self) -> int | None:
        return self.write_data_q if self.collision_q else self.banks[self.read_addr_q].read_data

    def edge(self, read: bool, read_addr: int, write: bool, write_addr: int,
             write_data: int, reset: bool = False) -> tuple[bool, int | None]:
        if not (0 <= read_addr < self.depth and 0 <= write_addr < self.depth):
            raise ValueError("address out of range")
        if not 0 <= write_data < (1 << self.width):
            raise ValueError("data exceeds word width")
        if reset:
            self.rd_valid = False
            # Ignore requests, preserving both memory and last output selection.
            return False, self.read_data
        collision = bool(read and write and read_addr == write_addr)
        for i, bank in enumerate(self.banks):
            bank_write = bool(write and write_addr == i)
            bank_read = bool(read and read_addr == i and not collision)
            bank.edge(bank_read, bank_write, write_data)
        self.rd_valid = bool(read)
        if read:
            self.read_addr_q = read_addr
            self.collision_q = collision
            if collision:
                self.write_data_q = write_data
        return self.rd_valid, self.read_data
