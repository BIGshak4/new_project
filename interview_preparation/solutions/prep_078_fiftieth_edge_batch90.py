"""Modulo50 event pulse. API call denotes one rising source-clock edge."""


def clock_pulses(cycles):
    if type(cycles) is not int or cycles < 0:
        raise ValueError("nonnegative cycle count required")
    phase = 0
    trace = []
    for _ in range(cycles):
        pulse = int(phase == 49)
        phase = 0 if pulse else phase + 1
        trace.append((pulse, phase))
    return trace


def input_event_pulses(samples):
    """Single clock domain; sampled event input must obey the sampling contract."""
    previous = phase = 0
    result = []
    for value in samples:
        if type(value) is not int or value not in (0, 1):
            raise ValueError("binary samples required")
        rising = value & (1 ^ previous)
        pulse = int(rising and phase == 49)
        if rising:
            phase = 0 if pulse else phase + 1
        previous = value
        result.append(pulse)
    return result


def divided_square(cycles):
    """Optional50% duty-cycle output: toggle every25 input rising edges."""
    phase = level = 0
    result = []
    for _ in range(cycles):
        if phase == 24:
            phase, level = 0, 1 ^ level
        else:
            phase += 1
        result.append(level)
    return result
