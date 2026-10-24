"""Variant D: marker-only local program; no meeting or position sensor.

    move_right()
    while not on_flag():
        wait_one_tick()
        move_right()
    while True:
        move_right()

Every loop iteration executes a timed action. Tests/control are instantaneous;
waiting and unit movement take one tick. Flags remain at the landing positions.
The simulator detects co-location for verification only, never for the program.
"""

from dataclasses import dataclass
from fractions import Fraction


@dataclass
class FlagProgram:
    started: bool = False
    fast: bool = False
    pending_move: bool = False

    def command(self, flag_here: bool) -> str:
        """Only one marker-presence bit enters the local controller."""
        if not self.started:
            self.started = True
            return "right"
        if self.pending_move:
            self.pending_move = False
            return "right"
        if flag_here:
            self.fast = True
        if self.fast:
            return "right"
        self.pending_move = True
        return "wait"


def simulate(distance: int, *, origin: int = 0, swapped: bool = False,
             max_ticks: int | None = None) -> dict:
    """Environment only: positions and collision detection are not controller inputs.

    A Fraction distance is accepted solely for explicit out-of-contract examples.
    The main guarantee is for nonnegative integer distances, common orientation,
    simultaneous start and identical action durations.
    """
    distance = Fraction(distance)
    if distance < 0:
        raise ValueError("distance must be nonnegative")
    positions = [Fraction(origin), Fraction(origin) + distance]
    if swapped:
        positions.reverse()
    flags = frozenset(positions)
    controllers = [FlagProgram(), FlagProgram()]
    if max_ticks is None:
        if distance.denominator != 1:
            raise ValueError("noninteger counterexamples require a finite test horizon")
        max_ticks = 4 * int(distance) + 4
    first_meeting = Fraction(0) if distance == 0 else None
    trajectory = [positions.copy()]
    actions = []
    for tick in range(max_ticks):
        commands = [controller.command(position in flags)
                    for controller, position in zip(controllers, positions, strict=True)]
        speeds = [int(command == "right") for command in commands]
        gap, closing = positions[1] - positions[0], speeds[0] - speeds[1]
        if first_meeting is None and closing:
            within_tick = gap / closing
            if 0 <= within_tick <= 1:
                first_meeting = Fraction(tick) + within_tick
        positions = [position + speed for position, speed in zip(positions, speeds, strict=True)]
        trajectory.append(positions.copy())
        actions.append(commands)
    return {"first_meeting": first_meeting, "trajectory": trajectory, "actions": actions,
            "controllers": controllers}
