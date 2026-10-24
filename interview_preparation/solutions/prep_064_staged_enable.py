"""Gate equations for separately enabled one/three-bit up and down counters.

Every call models one shared rising edge. Enable is sampled data, never clock.
Reset is an explicit added synchronous active-high convention.
"""


def next_state(state, enable, *, width=3, direction="up", reset=0):
    if type(width) is not int or width not in (1, 3):
        raise ValueError("this source variant uses width one or three")
    if type(state) is not int or not 0 <= state < (1 << width):
        raise ValueError("state outside selected unsigned width")
    if type(enable) is not int or enable not in (0, 1):
        raise ValueError("binary enable required")
    if type(reset) is not int or reset not in (0, 1):
        raise ValueError("binary reset required")
    if direction not in ("up", "down"):
        raise ValueError("separate up or down design required")
    if reset:
        return 0
    old = [(state >> index) & 1 for index in range(width)]
    lower_condition = enable
    output = 0
    for index, value in enumerate(old):
        output |= (value ^ lower_condition) << index
        lower_condition &= value if direction == "up" else (value ^ 1)
    return output
