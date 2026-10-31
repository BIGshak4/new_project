"""Declared Boolean and ideal-delay models for the 2026-10-31 intake.

These are executable study models, not synthesized RTL or safety-control code.
MUX(s,d0,d1) selects d0 at zero. Storage models require a known initial state.
"""
from __future__ import annotations


def mux(select: int, d0: int, d1: int) -> int:
    return d1 if select else d0


def fault_alert(heat: int, oil: int) -> int:
    """Active-high fault inputs; functional alert only, no vehicle actuation."""
    return heat | oil


def mux4_source(q0: int, q1: int, q2: int, q3: int, s1: int, s0: int) -> int:
    return mux(s1, mux(s0, q3, q2), mux(s0, q1, q0))


def mux4_standard(d0: int, d1: int, d2: int, d3: int, s1: int, s0: int) -> int:
    return mux(s1, mux(s0, d0, d1), mux(s0, d2, d3))


def full_adder(a: int, b: int, carry: int) -> tuple[int, int]:
    return a ^ b ^ carry, (a & b) | (a & carry) | (b & carry)


def add_2_to_4_ripple(a: int, b: int) -> int:
    carry, result = 0, 0
    for bit in range(4):
        total, carry = full_adder((a >> bit) & 1, (b >> bit) & 1, carry)
        result |= total << bit
    return result | (carry << 4)


def add_2_to_4_carry_select(a: int, b: int) -> int:
    low0, c1 = full_adder(a & 1, b & 1, 0)
    low1, c2 = full_adder((a >> 1) & 1, (b >> 1) & 1, c1)
    candidates = []
    for assumed in (0, 1):
        hi0, c3 = full_adder(0, (b >> 2) & 1, assumed)
        hi1, c4 = full_adder(0, (b >> 3) & 1, c3)
        candidates.append((hi0, hi1, c4))
    chosen = [mux(c2, candidates[0][i], candidates[1][i]) for i in range(3)]
    return low0 | (low1 << 1) | (chosen[0] << 2) | (chosen[1] << 3) | (chosen[2] << 4)


def zero_delay_mux_add(a: int, b: int) -> int:
    """Shannon tree of constants; shows why unrestricted zero-delay MUXes trivialize timing."""
    word = (a << 4) | b
    leaves = [(index >> 4) + (index & 15) for index in range(64)]
    for bit in range(6):
        leaves = [mux((word >> bit) & 1, leaves[i], leaves[i + 1])
                  for i in range(0, len(leaves), 2)]
    return leaves[0]


def mux_gates(a: int, b: int) -> dict[str, int]:
    nb = mux(b, 1, 0)
    return {"not_b": nb, "and": mux(a, 0, b), "or": mux(a, b, 1),
            "xor": mux(a, b, nb), "nand": mux(a, 1, nb)}


def latch_step(q: int, data: int, enable: int) -> int:
    return mux(enable, q, data)


def master_slave_step(master: int, q: int, data: int, clock: int) -> tuple[int, int]:
    complement = mux(clock, 1, 0)
    master = latch_step(master, data, complement)
    return master, latch_step(q, master, clock)


def isolate_lsb_serial(word: int, width: int = 20) -> int:
    lower_any, result = 0, 0
    for bit in range(width):
        value = (word >> bit) & 1
        result |= (value & (1 ^ lower_any)) << bit
        lower_any |= value
    return result


def isolate_lsb_balanced(word: int, width: int = 20) -> int:
    # Parallel prefix doubling: each stage doubles its covered lower interval.
    prefix = word & ((1 << width) - 1)
    distance = 1
    while distance < width:
        prefix |= prefix << distance
        distance *= 2
    return word & ~(prefix << 1) & ((1 << width) - 1)


def lsb_arrival_times(width: int = 20, balanced: bool = True) -> list[int]:
    # Arrival of a balanced fan-in-two OR of k inputs is ceil(log2 k).
    # y0 is a wire; all other outputs have NOT then AND after the lower OR.
    return [0] + [((bit - 1).bit_length() if balanced else bit - 1) + 2
                  for bit in range(1, width)]


def unsigned_gt_mux(a: int, b: int, width: int) -> int:
    greater = 0
    for bit in range(width):
        ai, bi = (a >> bit) & 1, (b >> bit) & 1
        greater = mux(ai ^ bi, greater, ai)
    return greater


def unsigned_gt_gate_tree(a: int, b: int, width: int) -> int:
    # Tuple (G,E) for one bit, then combine high and low adjacent blocks.
    blocks = [(((a >> bit) & 1) & (1 ^ ((b >> bit) & 1)),
               1 ^ (((a ^ b) >> bit) & 1)) for bit in range(width)]
    while len(blocks) > 1:
        next_level = []
        for index in range(0, len(blocks), 2):
            if index + 1 == len(blocks):
                next_level.append(blocks[index])
                continue
            gl, el = blocks[index]
            gh, eh = blocks[index + 1]
            next_level.append((gh | (eh & gl), eh & el))
        blocks = next_level
    return blocks[0][0]


def one_bit_gt_lt(a: int, b: int) -> tuple[int, int]:
    return a & (1 ^ b), (1 ^ a) & b
