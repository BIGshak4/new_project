"""Pure integer teaching models; HDL compilation is reported separately."""
def swap57(x):
    if type(x) is not int or not 0 <= x < 8:
        raise ValueError('three-bit unsigned input required')
    return x ^ (((x >> 2) & x & 1) << 1)


def half_adder(a, b):
    return a ^ b, a & b


def ha3(x):
    if type(x) is not int or not 0 <= x < 8:
        raise ValueError('three-bit unsigned input required')
    s, c1 = half_adder(x & 1, (x >> 1) & 1)
    low, c2 = half_adder(s, (x >> 2) & 1)
    high, unused = half_adder(c1, c2)
    return low + 2 * high, unused


def square_step(square, odd, width, reset=False):
    if type(width) is not int or width < 1:
        raise ValueError('positive register width required')
    mask = (1 << width) - 1
    if reset:
        return 0, 1
    return (square + odd) & mask, (odd + 2) & mask


def extended_step(low, high, load, data):
    if not 0 <= low < 16 or high not in (0, 1) or not 0 <= data < 32:
        raise ValueError('invalid width')
    return (data & 15, data >> 4) if load else ((low + 1) & 15, high ^ int(low == 15))


def phase_step(count, vin, reset=False):
    if count not in range(4) or vin not in (0, 1):
        raise ValueError('invalid phase state/input')
    return 0 if reset or not vin else min(3, count + 1)


def phase_output(count, vin, clk, reset=False):
    return int(not reset and clk and vin and count == 2)


# Editorial event coding, not a claim about the screenshot's binary encoding.
DELTAS = {0b1000: -1, 0b0100: 1, 0b0010: 1, 0b0001: -1, 0: 0}


def room_step(difference, event):
    return difference + DELTAS.get(event, 0)


def room_lights(difference):
    return int(difference > 0), int(difference == 0), int(difference < 0)
