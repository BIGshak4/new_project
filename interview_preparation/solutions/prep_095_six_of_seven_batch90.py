"""Assert after a full seven-sample sliding window contains at least six ones."""


def monitor(bits):
    history = 0
    count = filled = 0
    trace = []
    for bit in bits:
        if type(bit) is not int or bit not in (0, 1):
            raise ValueError("error samples must be binary integers")
        expired = (history >> 6) & 1
        history = ((history << 1) | bit) & 127
        count += bit - expired
        filled = min(7, filled + 1)
        alarm = int(filled == 7 and count >= 6)
        trace.append((alarm, count, filled, history))
    return trace
