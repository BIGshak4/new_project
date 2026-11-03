"""Independent scan-based oracle and semantic Sudoku result validation."""
import copy
import importlib.util
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sudoku_reference', ROOT / 'solutions/prep_245_sudoku.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def valid_completion(givens, result):
    if not isinstance(result, list) or len(result) != 9 or any(len(r) != 9 for r in result):
        return False
    expected = set(range(1, 10))
    groups = list(result) + [[result[r][c] for r in range(9)] for c in range(9)]
    groups += [[result[r + dr][c + dc] for dr in range(3) for dc in range(3)]
               for r in (0, 3, 6) for c in (0, 3, 6)]
    return (all(set(group) == expected for group in groups)
            and all(not givens[r][c] or givens[r][c] == result[r][c] for r in range(9) for c in range(9)))


def slow_oracle(board):
    work = copy.deepcopy(board)

    def fill():
        for r in range(9):
            for c in range(9):
                if work[r][c] == 0:
                    forbidden = set(work[r]) | {work[i][c] for i in range(9)}
                    forbidden |= {work[i][j] for i in range(r // 3 * 3, r // 3 * 3 + 3)
                                  for j in range(c // 3 * 3, c // 3 * 3 + 3)}
                    for digit in range(1, 10):
                        if digit not in forbidden:
                            work[r][c] = digit
                            if fill():
                                return True
                    work[r][c] = 0
                    return False
        return True

    return work if fill() else None


def run():
    solved = [[(r * 3 + r // 3 + c) % 9 + 1 for c in range(9)] for r in range(9)]
    rng = random.Random(245)
    cases = [solved, [[0] * 9 for _ in range(9)]]
    for holes in range(1, 21):
        for _ in range(10):
            board = copy.deepcopy(solved)
            for pos in rng.sample(range(81), holes):
                board[pos // 9][pos % 9] = 0
            cases.append(board)
    # Locally consistent givens, yet (0,8) has no possible digit.
    impossible = [[0] * 9 for _ in range(9)]
    impossible[0][:8] = list(range(1, 9))
    impossible[1][8] = 9
    cases.append(impossible)
    impossible_count = 0
    for board in cases:
        before = copy.deepcopy(board)
        actual = module.solve_sudoku(board)
        expected = slow_oracle(board)
        assert board == before
        if expected is None:
            assert actual is None
            impossible_count += 1
        else:
            assert valid_completion(board, actual)
    invalid = [[], [[0] * 8 for _ in range(9)], [[True] * 9 for _ in range(9)],
               [[10] * 9 for _ in range(9)]]
    duplicate = copy.deepcopy(solved)
    duplicate[0][1] = duplicate[0][0]
    invalid.append(duplicate)
    for board in invalid:
        try:
            module.solve_sudoku(board)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid board was accepted')
    result = {'question': 'PREP-245', 'valid_input_cases': len(cases), 'unsatisfiable_cases': impossible_count,
              'invalid_cases': len(invalid), 'oracle': 'independent scan/backtracking; semantic row/column/box/givens validation',
              'passed': True, 'scope': 'Python executed; finite samples, not exhaustive over all Sudoku puzzles'}
    (ROOT / 'checks/prep-245-verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    print(json.dumps(run()))
