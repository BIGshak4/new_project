def transpose_in_place(matrix):
    """Transpose a square list of distinct mutable rows and return it."""
    size = len(matrix)
    for row in range(size):
        for col in range(row + 1, size):
            matrix[row][col], matrix[col][row] = matrix[col][row], matrix[row][col]
    return matrix
