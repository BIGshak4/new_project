"""Destructive length discovery for a nonempty modulo-addressed bit memory."""


def discover_length(read, write):
    """Use only the supplied interface; write(i, v) accesses i modulo N."""
    write(0, 1)
    address = 1
    while True:
        write(address, 0)
        if read(0) == 0:
            return address
        address += 1


class CircularBits:
    """Executable specification, not a physical memory implementation."""

    def __init__(self, initial):
        if not initial or any(bit not in (0, 1) for bit in initial):
            raise ValueError("nonempty sequence of bits required")
        self.bits = list(initial)
        self.reads = self.writes = 0

    def read(self, address):
        if type(address) is not int or address < 0:
            raise ValueError("nonnegative integer address required")
        self.reads += 1
        return self.bits[address % len(self.bits)]

    def write(self, address, value):
        if type(address) is not int or address < 0 or value not in (0, 1):
            raise ValueError("nonnegative address and bit required")
        self.writes += 1
        self.bits[address % len(self.bits)] = value
