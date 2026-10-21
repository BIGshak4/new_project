"""Fixed blocks and sliding windows count sampled-high ERROR cycles.

Python integers model an unbounded cycle index. Both functions require binary
samples; a constant bit bound for timestamps is not claimed.
"""
from collections import deque
from collections.abc import Iterable


def fixed_block_results(
    samples: Iterable[int], window: int = 100_000, threshold: int = 10
) -> list[str]:
    """Report after each complete non-overlapping block; ignore a final tail."""
    _validate(window, threshold)
    count = cycles = 0
    results = []
    for error in samples:
        _binary(error)
        cycles += 1
        count = min(threshold + 1, count + error)
        if cycles == window:
            results.append("Failed" if count > threshold else "Passed")
            count = cycles = 0
    return results


def first_sliding_failure(
    samples: Iterable[int], window: int = 100_000, threshold: int = 10
) -> int | None:
    """First zero-based cycle with >threshold highs in its trailing window.

    Before a full window exists, only the observed prefix is counted. A failure
    then also implies failure in the first complete window if sampling continues.
    At most threshold+1 timestamps are retained; return immediately on failure.
    """
    _validate(window, threshold)
    recent: deque[int] = deque()
    for cycle, error in enumerate(samples):
        _binary(error)
        while recent and cycle - recent[0] >= window:
            recent.popleft()
        if error:
            recent.append(cycle)
            if len(recent) > threshold:
                return cycle
    return None


def _validate(window: int, threshold: int) -> None:
    if type(window) is not int or window < 1 or type(threshold) is not int or threshold < 0:
        raise ValueError("positive integer window and nonnegative integer threshold required")


def _binary(value: int) -> None:
    if value not in (0, 1):
        raise ValueError("samples must be binary")
