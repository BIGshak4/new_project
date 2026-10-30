"""Serialized landing-decision model, not deployable ISR or elevator firmware.

The source APIs do not supply doors, alignment, faults or braking guarantees.
control_step is called only at a known aligned landing, with commands taking
effect before departure. The event loop serializes button posts and steps.
A real ISR needs atomic fetch_or and an atomic exchange/drain, not this Python
read/modify/write. One task owns engine calls and sweep direction.
"""
from enum import IntEnum


class STATE(IntEnum):
    UP = 0
    DOWN = 1
    STOP = 2


class ElevatorController:
    def __init__(self, engine):
        self.engine = engine
        self.inbox = self.pending = 0
        self.direction = STATE.STOP

    def EnignePressedFloor(self, floor):
        """Preserve the source API typo; post a coalesced request only."""
        if type(floor) is not int or not 1 <= floor <= 8:
            raise ValueError("valid floors are one through eight")
        self.inbox |= 1 << (floor - 1)

    def control_step(self):
        # Serialized here; a real task must atomically exchange the ISR inbox.
        self.pending |= self.inbox
        self.inbox = 0
        floor = self.engine.EngineGetCurrFloor()
        state = self.engine.EngineStateGet()
        if type(floor) is not int or not 1 <= floor <= 8 or state not in STATE:
            raise ValueError("model requires a valid aligned landing and state")
        bit = 1 << (floor - 1)
        if self.pending & bit:
            self.engine.EngineStop()
            self.pending &= ~bit
            return floor  # Model service event; no door-open API is invented.
        if not self.pending:
            self.engine.EngineStop()
            self.direction = STATE.STOP
            return None
        below = self.pending & (bit - 1)
        above = self.pending & ~((bit << 1) - 1)
        if self.direction == STATE.UP:
            self.direction = STATE.UP if above else STATE.DOWN
        elif self.direction == STATE.DOWN:
            self.direction = STATE.DOWN if below else STATE.UP
        else:
            targets = [f for f in range(1, 9) if self.pending & (1 << (f - 1))]
            target = min(targets, key=lambda f: (abs(f - floor), f))
            self.direction = STATE.UP if target > floor else STATE.DOWN
        if self.direction == STATE.UP:
            self.engine.EngineUp()
        else:
            self.engine.EngineDown()
        return None
