"""Live-data disagreement until the next sampling edge; event order is explicit."""


def edge_events(events, initial=0):
    if initial not in (0, 1):
        raise ValueError('binary initial sample required')
    current = saved = initial
    out = []
    for kind, value in events:
        if kind == 'data' and value in (0, 1):
            current = value
        elif kind == 'clock':
            saved = current
        else:
            raise ValueError('data/clock event required; simultaneous events excluded')
        out.append([current & (1 - saved), saved & (1 - current), current ^ saved])
    return out
