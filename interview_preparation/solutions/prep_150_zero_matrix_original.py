"""Zero rows/columns containing ORIGINAL zeros; independent mutable rows.

Both functions mutate and return the same matrix. Rectangular list-of-lists
with integer values and nonaliased row storage is a precondition. Shape/type
validation precedes writes; aliasing is not checked using an O(R) identity set.
"""


def shape(matrix):
    if not isinstance(matrix, list):
        raise ValueError("matrix must be a list of rows")
    if not matrix:
        return 0, 0
    if not isinstance(matrix[0], list):
        raise ValueError("rows must be mutable lists")
    columns = len(matrix[0])
    for row in matrix:
        if not isinstance(row, list) or len(row) != columns:
            raise ValueError("rectangular mutable rows required")
    return len(matrix), columns


def zero_with_flags(matrix):
    rows, columns = shape(matrix)
    zero_rows, zero_columns = [False] * rows, [False] * columns
    for i in range(rows):
        for j in range(columns):
            if matrix[i][j] == 0:
                zero_rows[i] = zero_columns[j] = True
    for i in range(rows):
        for j in range(columns):
            if zero_rows[i] or zero_columns[j]:
                matrix[i][j] = 0
    return matrix


def zero_inplace_markers(matrix):
    rows, columns = shape(matrix)
    if rows == 0 or columns == 0:
        return matrix
    first_row = any(matrix[0][j] == 0 for j in range(columns))
    first_column = any(matrix[i][0] == 0 for i in range(rows))
    for i in range(1, rows):
        for j in range(1, columns):
            if matrix[i][j] == 0:
                matrix[i][0] = matrix[0][j] = 0
    for i in range(1, rows):
        for j in range(1, columns):
            if matrix[i][0] == 0 or matrix[0][j] == 0:
                matrix[i][j] = 0
    if first_row:
        for j in range(columns):
            matrix[0][j] = 0
    if first_column:
        for i in range(rows):
            matrix[i][0] = 0
    return matrix
