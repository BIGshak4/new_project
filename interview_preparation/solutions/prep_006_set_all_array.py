"""Logical fixed-size array: O(1) Set/Get/SetAll in the reference-RAM model.

Initialization is O(N). Values are object references, not deep copies.
No thread-safety or real-time Python runtime guarantee is implied.
"""


class SetAllArray:
    def __init__(self, initial_values):
        self._values = list(initial_values)
        self._epoch = object()
        self._stamps = [self._epoch] * len(self._values)
        self._all_value = None

    def _check_index(self, index):
        if not isinstance(index, int):
            raise TypeError("index must be an integer")
        if not 0 <= index < len(self._values):
            raise IndexError("index out of range")

    def Set(self, index, value):
        self._check_index(index)
        self._values[index] = value
        self._stamps[index] = self._epoch

    def Get(self, index):
        self._check_index(index)
        if self._stamps[index] is self._epoch:
            return self._values[index]
        return self._all_value

    def SetAll(self, value):
        self._all_value = value
        self._epoch = object()
