"""Counted MUX topology; equal-delay stable-select model, not physical STA."""


def mux(select, low, high):
    return high if select else low


def evaluate(data, select):
    if len(data) != 8 or any(v not in (0, 1) for v in data) or not 0 <= select < 8:
        raise ValueError('eight binary inputs and three-bit select required')
    s0, s1, s2 = [(select >> bit) & 1 for bit in range(3)]
    pairs = [mux(s0, data[i], data[i + 1]) for i in range(0, 8, 2)]
    balanced = mux(s2, mux(s1, *pairs[:2]), mux(s1, *pairs[2:]))
    # Prune the old D0/D1 MUX: D1 is safe when select=0 because the final
    # bypass chooses D0 in precisely that otherwise-don't-care case.
    rest = mux(s2, mux(s1, data[1], pairs[1]), mux(s1, pairs[2], pairs[3]))
    bypass = mux(int(select == 0), rest, data[0])
    return balanced, bypass


def worst_data_arrival(arrivals, cell_delay, optimized=False):
    if len(arrivals) != 8 or cell_delay < 0:
        raise ValueError('eight arrivals and nonnegative delay required')
    depths = [1, 3, 4, 4, 4, 4, 4, 4] if optimized else [3] * 8
    return max(a + depth * cell_delay for a, depth in zip(arrivals, depths))
