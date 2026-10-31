"""Count anonymous physical rooms using only movement and the current lamp.

The room interface exposes move_clockwise(), move_counterclockwise(),
lamp_is_on(), set_lamp(bool). It exposes no length, address or room identity.
Reliable reversible movement and exclusive control of lamps are assumed.
"""

def count_rooms(room):
    room.set_lamp(True)
    while True:
        steps = 0
        while True:
            room.move_clockwise()
            steps += 1
            if room.lamp_is_on():
                break
        room.set_lamp(False)
        for _ in range(steps):
            room.move_counterclockwise()
        if not room.lamp_is_on():
            return steps
