def count_boxes(box):
    """Each nonempty box holds one smaller box. None means no box."""
    if box is None:
        return 0
    return 1 + count_boxes(box["inside"])
