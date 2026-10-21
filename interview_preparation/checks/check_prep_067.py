"""Compare ring-memory FIFO against an independent deque oracle."""
import itertools
import json
import random
import sys
from collections import deque
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / 'solutions'))
from prep_067_fifo8 import Fifo8


def compare(fifo, queue, wr, rd, data, reset=False):
    old_out = fifo.dout
    n = len(queue)
    expected_pop = bool(not reset and rd and n)
    expected_push = bool(not reset and wr and (n < 8 or expected_pop))
    expected_out = queue.popleft() if expected_pop else old_out
    if reset:
        queue.clear()
        expected_out = 0
    elif expected_push:
        queue.append(data)
    assert fifo.tick(wr, rd, data, reset) == (expected_push, expected_pop)
    assert fifo.dout == expected_out and fifo.rd_valid == expected_pop
    assert fifo.count == len(queue) and 0 <= fifo.count <= 8
    assert fifo.write_ptr == (fifo.read_ptr + fifo.count) % 8
    logical = [fifo.memory[(fifo.read_ptr + i) % 8] for i in range(fifo.count)]
    assert logical == list(queue)


def main():
    exhaustive = resets = 0
    for n in range(9):
        for items in itertools.product(range(2), repeat=n):
            for rp in range(8):
                mem = [0] * 8
                for i, value in enumerate(items):
                    mem[(rp + i) % 8] = value
                for wr, rd, data in itertools.product(range(2), repeat=3):
                    for old_out in range(2):
                        f = Fifo8(1, mem.copy(), rp, (rp + n) % 8, n, old_out)
                        compare(f, deque(items), wr, rd, data)
                        exhaustive += 1
                for wr, rd in itertools.product(range(2), repeat=2):
                    f = Fifo8(1, mem.copy(), rp, (rp + n) % 8, n, 1)
                    compare(f, deque(items), wr, rd, 1, reset=True)
                    resets += 1
    rng = random.Random(67021)
    f, queue = Fifo8(16), deque()
    for _ in range(100_000):
        compare(f, queue, rng.randrange(2), rng.randrange(2), rng.randrange(65536), rng.randrange(97) == 0)
    evidence = {'question_id': 'PREP-067', 'status': 'passed',
                'exhaustive_one_bit_transition_cases': exhaustive, 'reset_priority_cases': resets,
                'sampled_sixteen_bit_edges': 100000, 'random_seed': 67021,
                'coverage': 'All logical one-bit queue contents of length 0..8, every read-pointer rotation, controls, input data and previous dout. Independent deque oracle; sampled wide-data long run includes reset and wrap.',
                'scope': 'Python model only. Supplied SystemVerilog was not compiled/simulated; RAM read-during-write and timing require technology-specific verification.'}
    (BANK / 'checks/prep-067-verification.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(evidence))


if __name__ == '__main__':
    main()
