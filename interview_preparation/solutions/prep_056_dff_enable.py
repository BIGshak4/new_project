"""Boolean next-state model for a D flip-flop with synchronous enable.

No clock gating; call once per rising clock edge. Initial q is supplied by the
caller, since an ordinary DFF without reset has no guaranteed power-up value.
"""


def next_q(q: int, data: int, en: int) -> int:
    if any(type(value) is not int or value not in (0, 1) for value in (q, data, en)):
        raise ValueError("q, data and en must be binary integers")
    return (en & data) | ((1 ^ en) & q)


def trace(initial_q, samples):
    q = initial_q
    output = []
    for data, en in samples:
        q = next_q(q, data, en)
        output.append(q)
    return output
