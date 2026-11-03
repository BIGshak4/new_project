"""Independent trusted November3 expected-value models, never learner code."""
import copy


def sudoku_oracle(board):
    """Scan-based enumerator, independent of masks/MRV; stop after two."""
    work = copy.deepcopy(board)
    answers = []

    def visit():
        for r in range(9):
            for c in range(9):
                if work[r][c] == 0:
                    used = set(work[r]) | {work[i][c] for i in range(9)}
                    used |= {work[i][j] for i in range(r // 3 * 3, r // 3 * 3 + 3)
                             for j in range(c // 3 * 3, c // 3 * 3 + 3)}
                    for digit in range(1, 10):
                        if digit not in used:
                            work[r][c] = digit
                            visit()
                            work[r][c] = 0
                            if len(answers) >= 2:
                                return
                    return
        answers.append(copy.deepcopy(work))

    visit()
    if len(answers) > 1:
        raise ValueError('exact-output runtime cases must have unique completions')
    return answers[0] if answers else None


def missing_oracle(values):
    present = set(values)
    return next(i for i in range(1, len(values) + 2) if i not in present)


def street_oracle(n, edges, people):
    distances = [[None] * n for _ in range(n)]
    for i in range(n):
        distances[i][i] = 0
    for u, v, length in edges:
        if distances[u][v] is None or length < distances[u][v]:
            distances[u][v] = distances[v][u] = length
    for k in range(n):
        for u in range(n):
            for v in range(n):
                if distances[u][k] is not None and distances[k][v] is not None:
                    candidate = distances[u][k] + distances[k][v]
                    if distances[u][v] is None or candidate < distances[u][v]:
                        distances[u][v] = candidate
    choices = [(sum(distances[p][v] for p in people), v) for v in range(n)
               if all(distances[p][v] is not None for p in people)]
    if not choices:
        return None
    score, vertex = min(choices)
    return [vertex, score]



ORACLES = {
    'prep-sudoku-backtracking-solver': sudoku_oracle,
    'prep-first-missing-positive-in-place': missing_oracle,
    'prep-street-network-meeting-median': street_oracle,
}
