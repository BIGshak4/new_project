def prefix_max_subarray_sums(values):
    """Immediately yield the best nonempty interval sum for each prefix."""
    stream = iter(values)
    first = next(stream, None)
    if first is None:
        return
    ending = best = first
    yield best
    for value in stream:
        ending = max(value, ending + value)
        best = max(best, ending)
        yield best
