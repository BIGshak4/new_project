"""Single-pass maximum nonempty contiguous sum with index-only output."""


def stream_maximum_subarray(values):
    """Return (sum, start, end_exclusive); ties prefer earlier start then end."""
    iterator = iter(values)
    try:
        current = next(iterator)
    except StopIteration as error:
        raise ValueError("nonempty input required") from error
    current_start = 0
    best_sum, best_start, best_end = current, 0, 1
    for index, value in enumerate(iterator, 1):
        if current < 0:
            current, current_start = value, index
        else:
            current += value
        if current > best_sum or (
            current == best_sum and (current_start, index + 1) < (best_start, best_end)
        ):
            best_sum, best_start, best_end = current, current_start, index + 1
    return best_sum, best_start, best_end
