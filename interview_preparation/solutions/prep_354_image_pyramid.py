"""Integer grayscale, edge replication, floor only after the complete 3x3 sum."""


def validate_levels(levels):
    if type(levels) is not int or levels < 0:
        raise ValueError("levels must be a nonnegative integer")


def checked_rows(rows):
    width = None
    found = False
    for row in rows:
        row = list(row)
        if width is None:
            width = len(row)
        if not width or len(row) != width:
            raise ValueError("nonempty rectangular image required")
        if any(type(value) is not int or not 0 <= value <= 255 for value in row):
            raise ValueError("pixels must be integers in 0..255")
        found = True
        yield row
    if not found:
        raise ValueError("nonempty image required")


def reduced_row(top, middle, bottom):
    width = len(middle)
    result = []
    for x in range(0, width, 2):
        left, right = max(0, x - 1), min(width - 1, x + 1)
        total = sum(row[left] + row[x] + row[right]
                    for row in (top, middle, bottom))
        result.append(total // 9)
    return result


def image_pyramid(image, levels):
    validate_levels(levels)
    current = list(checked_rows(image))
    result = [current]
    for _ in range(levels):
        height = len(current)
        current = [reduced_row(current[max(0, y - 1)], current[y],
                               current[min(height - 1, y + 1)])
                   for y in range(0, height, 2)]
        result.append(current)
    return result


class ReductionStage:
    def __init__(self):
        self.rows = []
        self.count = 0

    def push(self, row):
        self.rows.append(row)
        if len(self.rows) > 3:
            del self.rows[0]
        index = self.count
        self.count += 1
        if index % 2 == 1:
            top = self.rows[-3] if len(self.rows) == 3 else self.rows[0]
            return reduced_row(top, self.rows[-2], self.rows[-1])
        return None

    def finish(self):
        if self.count % 2:
            top = self.rows[-2] if len(self.rows) >= 2 else self.rows[-1]
            return reduced_row(top, self.rows[-1], self.rows[-1])
        return None


def stream_pyramid(rows, levels, emit):
    """emit(level, row) consumes a row immediately; this function stores no frames."""
    validate_levels(levels)
    stages = [ReductionStage() for _ in range(levels)]

    def deliver(level, row):
        # A loop propagates a row through levels without recursion-depth limits.
        while row is not None:
            emit(level, row.copy())
            if level == levels:
                return
            row = stages[level].push(row)
            level += 1

    for row in checked_rows(rows):
        deliver(0, row)
    for level, stage in enumerate(stages):
        row = stage.finish()
        if row is not None:
            deliver(level + 1, row)


def collect_stream_pyramid(rows, levels):
    validate_levels(levels)
    result = [[] for _ in range(levels + 1)]
    stream_pyramid(rows, levels, lambda level, row: result[level].append(row))
    return result
