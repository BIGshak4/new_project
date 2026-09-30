"""Verify all possible paths via exact set propagation and shortest strategy via BFS."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'solutions'))
from prep_029_moving_rabbit import PLAN,FULL,after_miss,trace,shortest_plan

def independent_step(states, shot):
    return {neighbor for pos in states if pos!=shot for neighbor in (pos-1,pos+1) if 1<=neighbor<=10}

for belief in range(1024):
    positions={i+1 for i in range(10) if belief & (1<<i)}
    for shot in range(1,11):
        expected=independent_step(positions,shot)
        assert after_miss(belief,shot)==sum(1<<(i-1) for i in expected)
for initial in range(1,11):
    assert trace(initial=1<<(initial-1))[-1]==0
assert len(PLAN)==16 and PLAN[7:9]==[9,9]
assert trace()[-1]==0 and all(trace()[i]!=0 for i in range(16))
even=sum(1<<(i-1) for i in range(2,11,2))
assert trace(PLAN[:8],even)[-1]==0
optimal,states=shortest_plan()
assert len(optimal)==16 and trace(optimal)[-1]==0
assert trace(list(range(1,11))*2)[-1]!=0
print(f'PASS: all 10240 state/action transitions, all 10 starts and compulsory-move paths; 16-shot plan catches all; BFS first goal depth 16 ({states} discovered states).')
