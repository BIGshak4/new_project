"""Ideal sampled one-shot model; not an analog circuit simulation."""

from dataclasses import dataclass


@dataclass
class Monostable:
    duration: int = 4
    retriggerable: bool = False
    previous: int = 0
    time: int = 0
    deadline: int | None = None

    def __post_init__(self):
        if self.duration < 1:
            raise ValueError("duration must be a positive integer number of ticks")

    def tick(self, vin: int, *, reset: bool = False) -> int:
        if vin not in (0, 1):
            raise ValueError("vin must already be thresholded to zero or one")
        now = self.time
        if self.deadline is not None and now >= self.deadline:
            self.deadline = None
        rising = self.previous == 0 and vin == 1
        if reset:
            self.deadline = None
        elif rising and (self.deadline is None or self.retriggerable):
            self.deadline = now + self.duration
        self.previous = vin
        self.time += 1
        return int(self.deadline is not None)


def waveform(inputs, duration=4, *, retriggerable=False, resets=()):
    device = Monostable(duration, retriggerable)
    reset_times = set(resets)
    return [device.tick(vin, reset=t in reset_times) for t, vin in enumerate(inputs)]
