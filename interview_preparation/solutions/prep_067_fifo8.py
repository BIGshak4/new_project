"""Eight-cell, common-clock FIFO reference model with registered read result."""
from dataclasses import dataclass, field


@dataclass
class Fifo8:
    width: int = 8
    memory: list[int] = field(default_factory=lambda: [0] * 8)
    read_ptr: int = 0
    write_ptr: int = 0
    count: int = 0
    dout: int = 0
    rd_valid: bool = False

    def __post_init__(self):
        if type(self.width) is not int or self.width < 1:
            raise ValueError("positive integer width required")

    def tick(self, wr_en: bool, rd_en: bool, din: int, rst: bool = False):
        if type(din) is not int or not 0 <= din < (1 << self.width):
            raise ValueError("din must fit the unsigned cell width")
        if rst:
            self.read_ptr = self.write_ptr = self.count = self.dout = 0
            self.rd_valid = False
            return False, False
        pop = bool(rd_en and self.count > 0)
        push = bool(wr_en and (self.count < 8 or pop))
        self.rd_valid = pop
        if pop:
            # Read old cell BEFORE a simultaneous write to the same address.
            self.dout = self.memory[self.read_ptr]
            self.read_ptr = (self.read_ptr + 1) % 8
        if push:
            self.memory[self.write_ptr] = din
            self.write_ptr = (self.write_ptr + 1) % 8
        self.count += int(push) - int(pop)
        return push, pop
