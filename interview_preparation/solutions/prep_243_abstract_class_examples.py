"""Python analogue of an abstract/concrete distinction, not a C++/C# runner."""
from abc import ABC, abstractmethod


class Shape(ABC):
    def label(self):
        return 'shape'

    @abstractmethod
    def area(self):
        raise NotImplementedError


class StillAbstract(Shape):
    pass


class Rectangle(Shape):
    def __init__(self, width, height):
        if width < 0 or height < 0:
            raise ValueError('Nonnegative dimensions required')
        self.width, self.height = width, height

    def area(self):
        return self.width * self.height


class Ordinary(ABC):
    """In Python, inheriting ABC alone does not make a class uninstantiable."""

    def area(self):
        return 0
