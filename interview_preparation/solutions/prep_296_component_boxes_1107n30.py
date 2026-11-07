"""Four-connected binary image components; inclusive bounding boxes."""
from collections import deque


def component_boxes(image):
    if type(image) is not list or any(type(row) is not list for row in image):
        raise ValueError("a rectangular list of bit rows is required")
    height = len(image)
    width = len(image[0]) if height else 0
    if (height and width == 0) or any(len(row) != width or any(type(v) is not int or v not in (0, 1) for v in row)
           for row in image):
        raise ValueError("a rectangular list of integer bits is required")
    seen = [[False] * width for _ in range(height)]
    boxes = []
    for row in range(height):
        for column in range(width):
            if image[row][column] == 0 or seen[row][column]:
                continue
            seen[row][column] = True
            queue = deque([(row, column)])
            low_row = high_row = row
            low_col = high_col = column
            while queue:
                r, c = queue.popleft()
                low_row, high_row = min(low_row, r), max(high_row, r)
                low_col, high_col = min(low_col, c), max(high_col, c)
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width and image[nr][nc] == 1
                            and not seen[nr][nc]):
                        seen[nr][nc] = True
                        queue.append((nr, nc))
            boxes.append([low_row, low_col, high_row, high_col])
    return boxes
