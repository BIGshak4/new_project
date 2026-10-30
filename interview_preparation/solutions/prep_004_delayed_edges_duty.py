"""Sampled both-edge detector with explicit extra-cycle pipeline latency."""


def delayed_edges(samples, initial=0):
    if initial not in (0, 1) or any(x not in (0, 1) for x in samples):
        raise ValueError("binary samples required")
    q1 = q2 = initial
    result = []
    for sample in samples:
        result.append(q1 ^ q2)
        q2, q1 = q1, sample
    return result


def steady_duty(period):
    """50% square wave, even integer sampled period >=2; omit startup."""
    if type(period) is not int or period < 2 or period % 2:
        raise ValueError("even sampled period required")
    word = [0] * (period // 2) + [1] * (period // 2)
    trace = delayed_edges(word * 4)
    tail = trace[2 * period:3 * period]
    return sum(tail), period
