"""Logical RAM fault-injection model; not a physical memory test qualification."""


class Memory:
    def __init__(self, alias_bit=None, stuck_zero_bit=None):
        self.words = [0] * 1024
        self.alias_bit = alias_bit
        self.stuck_zero_bit = stuck_zero_bit

    def address(self, address):
        return address if self.alias_bit is None else address & ~(1 << self.alias_bit)

    def write(self, address, value):
        if not 0 <= address < 1024 or not 0 <= value < 65536:
            raise ValueError("10 address and 16 data bits required")
        if self.stuck_zero_bit is not None:
            value &= ~(1 << self.stuck_zero_bit)
        self.words[self.address(address)] = value

    def read(self, address):
        if not 0 <= address < 1024:
            raise ValueError("10 address bits required")
        return self.words[self.address(address)]


def interface_tests(memory):
    """Destructive: assumes conventional, deterministic read/write operations."""
    for pattern in (0, 65535, 21845, 43690, *(1 << i for i in range(16))):
        for address in range(1024):
            memory.write(address, pattern)
        for address in range(1024):
            if memory.read(address) != pattern:
                return False
    # Each logical address receives a unique value before any is checked.
    for address in range(1024):
        memory.write(address, address)
    return all(memory.read(address) == address for address in range(1024))
