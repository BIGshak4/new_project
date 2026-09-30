"""Independent direct minimax plus exhaustive threshold searches."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'solutions'))
from prep_025_multiple_balls import coverage, minimum_drops, search

limit=150
dp=[[0]*(limit+1), list(range(limit+1))]
for balls in range(2,7):
    row=[0]*(limit+1)
    for n in range(1,limit+1):
        row[n]=min(1+max(dp[balls-1][floor-1],row[n-floor]) for floor in range(1,n+1))
    dp.append(row)
for balls in range(1,7):
    for n in range(limit+1):
        assert minimum_drops(n,balls)==dp[balls][n]
    worst=0
    for threshold in range(1,102):
        found, trace=search(100,balls,lambda f: f>=threshold)
        assert found==threshold
        assert len(trace)<=dp[balls][100]
        assert sum(broken for _,broken,_,_ in trace)<=balls
        assert all(1<=f<=100 and remaining_balls>0 and remaining_drops>0 for f,_,remaining_balls,remaining_drops in trace)
        worst=max(worst,len(trace))
    assert worst==dp[balls][100]
    print(f'{balls} balls: {minimum_drops(100,balls)} drops (no-break possible); {minimum_drops(99,balls)} (floor 100 guaranteed breaking)')
for balls in range(1,8):
    for drops in range(1,15):
        assert coverage(balls,drops)==1+coverage(balls-1,drops-1)+coverage(balls,drops-1)
assert [minimum_drops(100,b) for b in range(1,7)]==[100,14,9,8,7,7]
assert [minimum_drops(99,b) for b in range(1,7)]==[99,14,9,8,7,7]
print('PASS: independent minimax for 1..6 balls / 0..150 floors; all 606 100-floor threshold searches; coverage recurrence and known-top distinction.')
