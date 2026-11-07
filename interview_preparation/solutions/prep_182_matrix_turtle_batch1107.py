"""Finite rectangular board; reject an out-of-bounds M, no implicit wrapping."""
VECTORS = ((0, 1), (1, 0), (0, -1), (-1, 0))  # E,S,W,N


def returns_to_cell(matrix, row, column, heading, commands):
    if not matrix or not matrix[0] or any(len(r) != len(matrix[0]) for r in matrix):
        raise ValueError("nonempty rectangular matrix required")
    rows, columns = len(matrix), len(matrix[0])
    if (type(row) is not int or type(column) is not int or type(heading) is not int
            or not 0 <= row < rows or not 0 <= column < columns
            or not 0 <= heading < 4):
        raise ValueError("start cell or heading outside allowed domain")
    start_row, start_column = row, column
    for command in commands:
        if command == "R":
            heading = (heading + 1) % 4
        elif command == "L":
            heading = (heading - 1) % 4
        elif command == "M":
            dr, dc = VECTORS[heading]
            row, column = row + dr, column + dc
            if not 0 <= row < rows or not 0 <= column < columns:
                raise ValueError("movement leaves the finite board")
        else:
            raise ValueError("only R,L,M are allowed")
    return (row, column) == (start_row, start_column)
