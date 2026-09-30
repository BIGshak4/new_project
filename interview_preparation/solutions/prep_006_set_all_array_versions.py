"""Readable numeric-generation variant of PREP-006.

O(1) operations assume unit-cost generation arithmetic/comparison. Python integers
grow without overflow; for a strict fixed-size-reference formulation, use the
identity-token variant in prep_006_set_all_array.py.
"""


class SetAllArray:
    def __init__(self, values):
        self.values = list(values)
        self.generation = 0
        self.cell_generation = [0] * len(self.values)
        self.all_value = None

    def _check_index(self, index):
        if not isinstance(index, int):
            raise TypeError("index must be an integer")
        if not 0 <= index < len(self.values):
            raise IndexError("index out of range")

    def Set(self, index, value):
        self._check_index(index)
        self.values[index] = value
        self.cell_generation[index] = self.generation

    def Get(self, index):
        self._check_index(index)
        if self.cell_generation[index] == self.generation:
            return self.values[index]
        return self.all_value

    def SetAll(self, value):
        self.all_value = value
        self.generation += 1
