"""PREP-053: clocked model; inputs are already synchronized and debounced.

Reset only with both sensors clear and a known initial occupancy. A is outside,
B inside. A single passage must include the 11 overlap state. An invalid sample
or count bound failure permanently invalidates the count until a trusted reset.
"""
from dataclasses import dataclass


# Each row lists next states for AB = 00, 01, 10, 11, respectively.
# A completed traversal returns to IDLE and creates exactly one event.
NEXT = {
    "IDLE": ("IDLE", "X1", "E1", "WAIT_CLEAR"),
    "E1": ("IDLE", "WAIT_CLEAR", "E1", "E2"),
    "E2": ("WAIT_CLEAR", "E3", "E1", "E2"),
    "E3": ("IDLE", "E3", "WAIT_CLEAR", "E2"),
    "X1": ("IDLE", "X1", "WAIT_CLEAR", "X2"),
    "X2": ("WAIT_CLEAR", "X1", "X3", "X2"),
    "X3": ("IDLE", "WAIT_CLEAR", "X3", "X2"),
    "WAIT_CLEAR": ("IDLE", "WAIT_CLEAR", "WAIT_CLEAR", "WAIT_CLEAR"),
}


@dataclass
class DoorwayCounter:
    count: int = 0
    maximum: int = 255
    state: str = "IDLE"
    count_valid: bool = True

    def __post_init__(self):
        if not 0 <= self.count <= self.maximum:
            raise ValueError("Initial occupancy must fit the counter")

    def sample(self, a: int, b: int) -> int:
        """Return accepted +1/-1/0 event. Sticky validity is separate from count."""
        if a not in (0, 1) or b not in (0, 1):
            raise ValueError("Sensors are binary")
        ab = (a << 1) | b
        old = self.state
        new = NEXT[old][ab]
        event = 1 if old == "E3" and ab == 0 else -1 if old == "X3" and ab == 0 else 0
        if new == "WAIT_CLEAR" and old != "WAIT_CLEAR":
            self.count_valid = False
        self.state = new
        if event and not 0 <= self.count + event <= self.maximum:
            self.count_valid = False
            return 0  # Hold, never wrap or silently produce a negative occupancy.
        self.count += event
        return event


if __name__ == "__main__":
    counter = DoorwayCounter()
    for ab in (0b00, 0b10, 0b11, 0b01, 0b00):
        event = counter.sample(ab >> 1, ab & 1)
        print(f"AB={ab:02b} state={counter.state:10} event={event:+d} count={counter.count}")
