"""Distinct API variant: motion/wait take one tick; queries/control are free.

The program sees only on_parachute/did_meet, never position, ID or distance.
The harness knows coordinates solely to supply sensor values and track meeting.
"""
from dataclasses import dataclass
from fractions import Fraction


@dataclass
class RobotProgram:
    started: bool = False
    fast: bool = False
    pending_wait: bool = False

    def command(self, on_parachute: bool, did_meet: bool) -> str:
        if did_meet:
            return "stop"
        if not self.started:
            self.started = True
            return "move_right"  # Leave own marker before testing it.
        if self.pending_wait:
            self.pending_wait = False
            return "move_right"
        if not self.fast and on_parachute:
            self.fast = True
        if self.fast:
            return "move_right"
        self.pending_wait = True
        return "no_operation"


def meeting_offset(relative_position: int, relative_velocity: int) -> Fraction | None:
    """First co-location time in a unit segment, if it occurs."""
    if relative_position == 0:
        return Fraction(0)
    if relative_velocity:
        offset = Fraction(-relative_position, relative_velocity)
        if 0 <= offset <= 1:
            return offset
    return None


def simulate(distance: int, origin: int = 0, swapped: bool = False) -> Fraction:
    if distance < 0:
        raise ValueError("nonnegative integer separation required")
    positions = [origin, origin + distance]
    if swapped:
        positions.reverse()
    markers = set(positions)
    programs = [RobotProgram(), RobotProgram()]
    if distance == 0:
        assert all(p.command(True, True) == "stop" for p in programs)
        return Fraction(0)
    for tick in range(4 * distance + 2):
        commands = [p.command(x in markers, False)
                    for p, x in zip(programs, positions, strict=True)]
        velocities = [int(command == "move_right") for command in commands]
        relative_position = positions[0] - positions[1]
        relative_velocity = velocities[0] - velocities[1]
        offset = meeting_offset(relative_position, relative_velocity)
        if offset is not None:
            return tick + offset
        positions = [x + v for x, v in zip(positions, velocities, strict=True)]
    raise AssertionError("meeting bound exceeded")
