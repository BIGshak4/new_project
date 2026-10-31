"""Three-cell NAND, with an exact small-library lower-bound enumeration."""
from itertools import combinations_with_replacement, product


def a_cell(x, y):
    return 1 if x == y == 0 else 'Z'


def b_cell(x, y):
    return 0 if x == y == 1 else 'Z'


def drivers(x, y):
    return [a_cell(x, x), a_cell(y, y), b_cell(x, y)]


def nand(x, y):
    active = {value for value in drivers(x, y) if value != 'Z'}
    assert len(active) == 1
    return active.pop()


def minimum_direct_cover(free_constants=False):
    # Truth rows are 00,01,10,11. Driver choice is kind + two Boolean input nets.
    inputs = [(0,0,1,1), (0,1,0,1)]
    if free_constants:
        inputs += [(0,0,0,0), (1,1,1,1)]
    cells = []
    for function, x, y in product((a_cell, b_cell), inputs, inputs):
        values = tuple(function(a, b) for a, b in zip(x, y, strict=True))
        if values not in cells:
            cells.append(values)
    for size in range(1, 4):
        for chosen in combinations_with_replacement(cells, size):
            out = []
            for row in range(4):
                active = {cell[row] for cell in chosen if cell[row] != 'Z'}
                if len(active) != 1:
                    break
                out.append(active.pop())
            if out == [1,1,1,0]:
                return size
    raise AssertionError('No NAND cover within three cells')
