from collections import deque


class RandomLastFive:
    """Keep a separate history for each fixed inclusive range and instance."""

    def __init__(self, low, high, rand):
        if high - low + 1 < 6:
            raise ValueError('at least six values are required')
        self.low = low
        self.high = high
        self.rand = rand
        self.history = deque(maxlen=5)

    def next(self):
        high_rank = self.high - self.low - len(self.history)
        rank = self.rand(0, high_rank)
        if not 0 <= rank <= high_rank:
            raise ValueError('rand returned a rank outside the requested range')
        value = self.low + rank
        for excluded in sorted(self.history):
            if excluded > value:
                break
            value += 1
        self.history.append(value)
        return value


def random_from_ranks(low, high, ranks):
    """Deterministic adapter with zero-based ranks supplied for successive draws."""
    draws = iter(ranks)
    generator = RandomLastFive(low, high, lambda _lo, _hi: next(draws))
    return [generator.next() for _ in ranks]
