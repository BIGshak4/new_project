"""Ideal settled-state SR storage; invalid requests are rejected, not predicted.

The basic cross-coupled NOR circuit is a level-sensitive latch, not an edge FF.
The gate-built master/slave extension below uses a next-state equation followed
by opposite-phase D latches. Analog power-up, races and metastability are absent.
"""


def require_bit(value):
    if type(value) is not int or value not in (0, 1):
        raise ValueError("expected integer bit 0 or 1")
    return value


def sr_latch(q, set_bit, reset_bit):
    q, s, r = map(require_bit, (q, set_bit, reset_bit))
    if s and r:
        raise ValueError("S=R=1 is outside the NOR latch's valid memory contract")
    return s | (q & (r ^ 1))


def gated_sr_latch(q, set_bit, reset_bit, enable):
    q, s, r, en = map(require_bit, (q, set_bit, reset_bit, enable))
    return sr_latch(q, s & en, r & en)


def master_slave_phase(master, q, set_bit, reset_bit, clock):
    """Conceptual gate-built D-master/D-slave extension for rising-edge SR.

    S,R must be valid at active capture; rejecting 11 in either phase is this
    harness's deliberately stronger legal-input convention, not analog behavior.
    The master is transparent low; slave transparent high. No overlap is modeled.
    """
    master, q, s, r, clk = map(require_bit, (master, q, set_bit, reset_bit, clock))
    desired = sr_latch(q, s, r)  # Gate function S OR (Q AND NOT R).
    if clk == 0:
        master = desired
    else:
        q = master
    return master, q
