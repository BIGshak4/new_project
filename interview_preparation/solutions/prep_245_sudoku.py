"""Find any 9x9 completion; duplicate givens are invalid, not unsatisfiable."""
FULL = (1 << 9) - 1


def solve_sudoku(board):
    if (not isinstance(board, list) or len(board) != 9
            or any(not isinstance(row, list) or len(row) != 9 for row in board)):
        raise ValueError('a 9x9 list of rows is required')
    if any(type(v) is not int or not 0 <= v <= 9 for row in board for v in row):
        raise ValueError('cells must be integers 0..9; zero means empty')
    work = [row[:] for row in board]
    rows, cols, boxes = [0] * 9, [0] * 9, [0] * 9
    empty = []
    for r in range(9):
        for c in range(9):
            value, b = work[r][c], (r // 3) * 3 + c // 3
            if not value:
                empty.append((r, c))
                continue
            bit = 1 << (value - 1)
            if (rows[r] | cols[c] | boxes[b]) & bit:
                raise ValueError('duplicate givens in a row, column or box')
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit

    def visit(k):
        if k == len(empty):
            return True
        best, choices, size = k, 0, 10
        for i in range(k, len(empty)):
            r, c = empty[i]
            mask = FULL & ~(rows[r] | cols[c] | boxes[(r // 3) * 3 + c // 3])
            count = mask.bit_count()
            if count < size:
                best, choices, size = i, mask, count
            if size == 0:
                break
        if size == 0:
            return False
        empty[k], empty[best] = empty[best], empty[k]
        r, c = empty[k]
        b = (r // 3) * 3 + c // 3
        while choices:
            bit = choices & -choices
            choices ^= bit
            work[r][c] = bit.bit_length()
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit
            if visit(k + 1):
                return True
            rows[r] ^= bit
            cols[c] ^= bit
            boxes[b] ^= bit
            work[r][c] = 0
        empty[k], empty[best] = empty[best], empty[k]
        return False

    return work if visit(0) else None
