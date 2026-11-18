"""Contiguous, non-overlapping assignments. A zero-size client still needs a real base address."""


def partition(n, m, randomize=None):
    """Return (size, adrs) in client order. randomize(a,b) draws inclusively."""
    if n < 0 or m < 0 or (n and not m):
        raise ValueError("invalid dimensions")
    if not n:
        return [], []
    if randomize is None:
        base_size, extra = divmod(m, n)
        sizes = [base_size + (i < extra) for i in range(n)]
        bases = []
        cursor = 0
        for size in sizes:
            bases.append(min(cursor, m - 1))
            cursor += size
        return sizes, bases

    cuts = sorted(randomize(0, m) for _ in range(2 * n))
    clients = list(range(n))
    for last in range(n - 1, 0, -1):
        j = randomize(0, last)
        clients[last], clients[j] = clients[j], clients[last]
    sizes, bases = [0] * n, [0] * n
    for i, client in enumerate(clients):
        start, stop = cuts[2*i:2*i+2]
        sizes[client] = stop - start
        bases[client] = start if start < stop else randomize(0, m - 1)
    return sizes, bases

