def shelf_placements(width, height, get_next):
    """Yield [input index, x, y] for each placement on a fixed board."""
    x = base = shelf_height = 0
    index = 0
    while width > 0 and height > 0:
        piece = get_next()
        if piece is None:
            return
        w, h = piece
        current = index
        index += 1
        if not (0 < w <= width and 0 < h <= height - base):
            continue
        if w > width - x:
            new_base = base + shelf_height
            if h > height - new_base:
                continue
            x, base, shelf_height = 0, new_base, 0
        yield [current, x, base]
        x += w
        shelf_height = max(shelf_height, h)
        if x == width and base + shelf_height == height:
            return


def pack_shelves(width, height, pieces):
    source = iter(pieces)
    return list(shelf_placements(width, height, lambda: next(source, None)))
