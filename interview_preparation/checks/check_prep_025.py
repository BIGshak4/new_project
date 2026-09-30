"""Exhaust all thresholds and compare the drop bound to independent minimax DP."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'solutions'))
from prep_025_two_crystal_balls import find_threshold, min_drops

dp = [0]
cases = 0
for floors in range(201):
    if floors:
        # If first ball breaks, one remaining ball must scan f-1 unknown floors.
        dp.append(min(1 + max(f - 1, dp[floors - f]) for f in range(1, floors + 1)))
    assert min_drops(floors) == dp[floors]
    worst = 0
    for threshold in range(1, floors + 2):
        result, trace = find_threshold(floors, lambda f: f >= threshold)
        assert result == threshold
        assert all(1 <= f <= floors for _, f, _ in trace)
        dead = set()
        for ball, floor, broken in trace:
            assert ball not in dead
            assert broken == (floor >= threshold)
            if broken:
                dead.add(ball)
        assert len(dead) <= 2
        assert len(trace) <= dp[floors]
        worst = max(worst, len(trace))
        cases += 1
    assert worst == dp[floors]
assert min_drops(100) == 14
_, trace = find_threshold(100, lambda f: False)
assert [f for _, f, _ in trace] == [14,27,39,50,60,69,77,84,90,95,99,100]
assert len(find_threshold(100, lambda f: f >= 14)[1]) == 14
print(f'PASS: {cases} threshold scenarios for 0..200 floors, independent minimax comparison, ball lifecycle, and 100-floor schedule; exact optimum 14.')
