"""Check the FSM and map its CW/CCW convention to disk geometry."""

import importlib.util
import math
from pathlib import Path
import random

path = Path(__file__).resolve().parents[1] / "solutions" / "prep_007_rotation_fsm.py"
spec = importlib.util.spec_from_file_location("rotation_solution", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

cw_cycle = [0, 1, 3, 2]
ccw_cycle = [0, 2, 3, 1]
cw_edges = set(zip(cw_cycle, cw_cycle[1:] + cw_cycle[:1]))
ccw_edges = set(zip(ccw_cycle, ccw_cycle[1:] + ccw_cycle[:1]))
for previous in range(4):
    for current in range(4):
        edge = (previous, current)
        expected = "NO_CHANGE" if previous == current else "CW" if edge in cw_edges else "CCW" if edge in ccw_edges else "INVALID"
        assert module.classify(previous, current) == expected

fsm = module.RotationFSM()
assert fsm.step(1, 1) == "UNKNOWN"
assert fsm.step(1, 1) == "NO_CHANGE"
assert fsm.step(0, 0) == "INVALID"
assert fsm.step(0, 1) == "CW"

rng = random.Random(7007)
fsm = module.RotationFSM()
position = 0
assert fsm.step(0, 0) == "UNKNOWN"
for _ in range(10000):
    movement = rng.choice((-1, 0, 1))
    position = (position + movement) % 4
    current = cw_cycle[position]
    expected = "NO_CHANGE" if movement == 0 else "CW" if movement == 1 else "CCW"
    assert fsm.step(current >> 1, current & 1) == expected

# Representative angles consistent with the drawing, not measured dimensions.
# Mathematical angles increase counterclockwise; the initial upper half is black.
def sensors(theta):
    def black(sensor_angle):
        return int(0 <= ((sensor_angle - theta) % (2 * math.pi)) < math.pi)
    return black(math.radians(195)), black(math.radians(220))

for sign, direction, cycle in ((1, "CCW", ccw_cycle), (-1, "CW", cw_cycle)):
    fsm = module.RotationFSM()
    a, b = sensors(0)
    assert fsm.step(a, b) == "UNKNOWN"
    states = [(a << 1) | b]
    for sample in range(1, 3601):
        a, b = sensors(sign * sample * 2 * math.pi / 3600)
        result = fsm.step(a, b)
        if result != "NO_CHANGE":
            assert result == direction
            states.append((a << 1) | b)
    assert states == cycle + cycle[:1], states

print("PASS: all 16 transitions, initialization, invalid-jump recovery, 10000 reversible/steady steps, and 3600 angular steps per direction.")
print("Scope: ideal logical and geometric model; no noise, metastability or physical sampling-rate guarantee.")
