"""Check the strategy, not a computational lower-bound proof."""

from itertools import permutations
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'solutions'))
from prep_009_horse_races import fastest_three


def check(order):
    rank = {horse: position for position, horse in enumerate(order)}
    history = []

    def race(horses):
        assert len(horses) == len(set(horses)) == 5
        result = sorted(horses, key=rank.__getitem__)
        history.append(result)
        return result

    assert fastest_three(list(range(25)), race) == list(order[:3])
    assert len(history) == 7
    assert set(history[-1]).issuperset(order[1:3])


if __name__ == '__main__':
    count = 0
    # Every ordered placement of the true top three; remaining ranks fixed.
    for first_three in permutations(range(25), 3):
        order = list(first_three) + [h for h in range(25) if h not in first_three]
        check(order)
        count += 1
    rng = random.Random(9025)
    for _ in range(10000):
        order = list(range(25))
        rng.shuffle(order)
        check(order)
        count += 1
    print(f'PASS: {count} speed orders, exactly seven legal races each; ranked top three correct.')
