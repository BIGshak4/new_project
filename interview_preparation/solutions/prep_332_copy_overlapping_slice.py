def copy_within(values, source, size, target):
    """Copy one fixed-size slice with snapshot semantics and constant scratch."""
    length = len(values)
    if size < 0 or not 0 <= source <= length or not 0 <= target <= length:
        raise ValueError('invalid slice')
    if size > length - source or size > length - target:
        raise ValueError('slice exceeds array bounds')
    if size == 0 or target == source:
        return
    backwards = source < target < source + size
    offsets = range(size - 1, -1, -1) if backwards else range(size)
    for offset in offsets:
        values[target + offset] = values[source + offset]


def copied_array(values, source, size, target):
    """Return the JSON-visible array after the requested in-place operation."""
    copy_within(values, source, size, target)
    return values
