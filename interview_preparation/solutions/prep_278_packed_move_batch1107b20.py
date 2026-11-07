"""Stable clockwise move of one bit in 1024 LSB-first packed bits."""


def move_bit(data, x, y):
    if (type(data) is not list or len(data) != 128
            or any(type(v) is not int or not 0 <= v <= 255 for v in data)):
        raise ValueError("data must contain exactly 128 unsigned bytes")
    if type(x) is not int or type(y) is not int or not 0 <= x < 1024 or not 0 <= y < 1024:
        raise ValueError("x and y must be integers in 0..1023")

    def get(index):
        return (data[index >> 3] >> (index & 7)) & 1

    def put(index, bit):
        byte, mask = index >> 3, 1 << (index & 7)
        data[byte] = (data[byte] & (255 ^ mask)) | (bit << (index & 7))

    saved = get(x)
    for step in range(y):
        put((x + step) & 1023, get((x + step + 1) & 1023))
    put((x + y) & 1023, saved)
    return data
