"""Clock-edge model: two W-bit registers implementing Fibonacci modulo 2**W."""


class FibonacciRegisters:
    def __init__(self, width: int = 16):
        if type(width) is not int or width < 1:
            raise ValueError("width must be a positive integer")
        self.width = width
        self.mask = (1 << width) - 1
        self.a = 0
        self.b = 1

    @property
    def value(self) -> int:
        return self.a

    def step(self, reset: bool = False) -> int:
        if reset:
            self.a, self.b = 0, 1
        else:
            self.a, self.b = self.b, (self.a + self.b) & self.mask
        return self.value
