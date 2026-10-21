"""Gate-equivalent synchronous 3-bit up/down counter (modulo eight).

No arithmetic counter operation in the proposed next-state datapath. Inputs
are sampled together at an edge. Synchronous reset overrides both controls.
"""


def toggle_bits(q: int, inc: int, dec: int) -> tuple[int, int, int]:
    if type(q) is not int or not 0 <= q < 8:
        raise ValueError("q must be an integer from zero through seven")
    if any(type(v) is not int or v not in (0, 1) for v in (inc, dec)):
        raise ValueError("inc and dec must be integer bits")
    q0, q1 = q & 1, (q >> 1) & 1
    up = inc & (1 ^ dec)
    down = dec & (1 ^ inc)
    t0 = up | down
    t1 = (up & q0) | (down & (1 ^ q0))
    t2 = (up & q1 & q0) | (down & (1 ^ q1) & (1 ^ q0))
    return t0, t1, t2


def next_q(q: int, inc: int, dec: int, *, reset: bool = False) -> int:
    toggles = toggle_bits(q, inc, dec)
    if reset:
        return 0
    answer = 0
    for index, toggle in enumerate(toggles):
        answer |= (((q >> index) & 1) ^ toggle) << index
    return answer


if __name__ == "__main__":
    q = 0
    for inc, dec in [(1, 0)] * 9 + [(0, 1)] * 3:
        q = next_q(q, inc, dec)
        print(f"inc={inc}, dec={dec} -> q={q:03b}")
