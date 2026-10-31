"""Reverse columns within every row; retain row order and matrix shape."""


def reverse_columns(matrix):
    if not matrix or not matrix[0]:
        raise ValueError("hardware model requires positive row and column counts")
    columns = len(matrix[0])
    if any(len(row) != columns or any(bit not in (0, 1) for bit in row) for row in matrix):
        raise ValueError("rectangular binary matrix required")
    return [[matrix[row][columns - 1 - col] for col in range(columns)]
            for row in range(len(matrix))]


def flat_wire_index(row, col, columns):
    return row * columns + columns - 1 - col
