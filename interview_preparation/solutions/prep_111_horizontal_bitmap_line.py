"""Draw into an existing bytearray: MSB-first, padded rows, no clipping.

Screen metadata is established once. draw_horizontal(x,y,length) sets exactly
that half-open pixel range, preserving all other pixels, padding and extra bytes.
Invalid arguments raise ValueError before any buffer write.
"""


class MonoScreen:
    def __init__(self, buffer, width, height, pitch):
        if not isinstance(buffer, bytearray):
            raise ValueError("buffer must be a mutable bytearray")  # noqa: TRY004 - one documented rejection type.
        if any(type(value) is not int for value in (width, height, pitch)):
            raise ValueError("screen dimensions must be integers")
        if width <= 0 or height <= 0 or pitch < (width + 7) // 8:
            raise ValueError("invalid dimensions or row pitch")
        if len(buffer) < pitch * height:
            raise ValueError("buffer is shorter than its screen metadata")
        self.buffer = buffer
        self.width, self.height, self.pitch = width, height, pitch

    def draw_horizontal(self, x, y, length):
        if any(type(value) is not int for value in (x, y, length)):
            raise ValueError("coordinates and length must be integers")
        if not (0 <= y < self.height and 0 <= x <= self.width
                and 0 <= length <= self.width - x):
            raise ValueError("line must be wholly inside the screen")
        if length == 0:
            return
        first, last = x // 8, (x + length - 1) // 8
        row = y * self.pitch
        first_mask = 0xFF >> (x % 8)
        last_mask = (0xFF << (7 - ((x + length - 1) % 8))) & 0xFF
        if first == last:
            self.buffer[row + first] |= first_mask & last_mask
        else:
            self.buffer[row + first] |= first_mask
            for column in range(first + 1, last):
                self.buffer[row + column] = 0xFF
            self.buffer[row + last] |= last_mask
