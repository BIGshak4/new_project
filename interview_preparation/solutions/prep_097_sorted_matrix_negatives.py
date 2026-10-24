"""Count negatives in a rectangular, row/column nondecreasing matrix.

Sortedness and exact integer entries are preconditions, not scanned for validation.
The input is not mutated. Ragged rows are rejected in O(rows) time.
"""


def count_negatives(matrix):
    if not matrix:
        return 0
    columns = len(matrix[0])
    if any(len(row) != columns for row in matrix):
        raise ValueError("matrix must be rectangular")
    row, column, total = len(matrix) - 1, 0, 0
    while row >= 0 and column < columns:
        if matrix[row][column] < 0:
            total += row + 1
            column += 1
        else:
            row -= 1
    return total
