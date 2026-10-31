"""Old-state capture models: parallel copy and LSB-first recirculating copy."""


def parallel(a, b, width):
    mask = (1 << width) - 1
    if width < 1 or (a | b) & ~mask:
        raise ValueError('Positive width and unsigned words required')
    return a, a


def serial(a, b, width):
    mask = (1 << width) - 1
    if width < 1 or (a | b) & ~mask:
        raise ValueError('Positive width and unsigned words required')
    trace = [(a, b)]
    for _ in range(width):
        bit = a & 1
        a, b = (a >> 1) | (bit << (width - 1)), (b >> 1) | (bit << (width - 1))
        trace.append((a, b))
    return a, b, trace
