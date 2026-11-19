"""Independent expected outputs for three software interview exercises."""


def median(values):
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) % 2:
        return ordered[len(ordered) // 2]
    return (ordered[(len(ordered) - 1) // 2] + ordered[len(ordered) // 2]) / 2


def accepts_frame(transmission):
    payload, terminator, _tail = transmission.partition("\\")
    n = len(payload) // 3
    return bool(terminator) and payload == "x" * n + "y" * (2 * n)


def pack_shelves(width, height, pieces):
    shelves = [[]]
    placements = []
    for index, (w, h) in enumerate(pieces):
        if not (0 < w <= width and 0 < h <= height):
            continue
        base = sum(max(pair[1] for pair in row) for row in shelves[:-1])
        if h > height - base:
            continue
        row = shelves[-1]
        start = sum(pair[0] for pair in row)
        if start + w > width:
            next_base = base + max(pair[1] for pair in row)
            if next_base + h > height:
                continue
            start, base = 0, next_base
            row = []
            shelves.append(row)
        placements.append([index, start, base])
        row.append((w, h))
    return placements


ORACLES = {
    "prep-median-of-unsorted-array": median,
    "prep-recognize-ordered-double-y-stream": accepts_frame,
    "prep-online-rectangle-shelf-placement": pack_shelves,
}
