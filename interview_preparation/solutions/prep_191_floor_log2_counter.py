"""Clocked 16-bit floor-log2 reference model; no floating-point arithmetic."""

from dataclasses import dataclass


@dataclass
class FloorLog2Counter:
    work: int = 0
    count: int = 0
    result: int = 0
    busy: bool = False
    done: bool = False
    valid: bool = False

    def tick(self, value: int = 0, *, start: bool = False, reset: bool = False):
        if not 0 <= value < 1 << 16:
            raise ValueError("value must be an unsigned 16-bit integer")
        self.done = False
        if reset:
            self.work = self.count = self.result = 0
            self.busy = self.valid = False
        elif self.busy:
            if self.work > 1:
                self.work >>= 1
                self.count += 1
            else:
                self.result = self.count
                self.busy = False
                self.done = self.valid = True
        elif start:
            self.work, self.count = value, 0
            self.valid = False
            if value == 0:
                self.result = 0  # deterministic placeholder, not log2(0)
                self.done = True
            else:
                self.busy = True
        return {"result": self.result, "busy": self.busy, "done": self.done, "valid": self.valid}


def floor_log2(value: int):
    device = FloorLog2Counter()
    device.tick(value, start=True)
    cycles = 0
    while device.busy:
        device.tick()
        cycles += 1
    return device.result, device.valid, cycles
